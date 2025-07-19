# core/ai_risk_detection.py

from django.db.models import Avg, Count, StdDev, Q
from django.utils import timezone
from datetime import timedelta, date
from typing import Dict, List, Tuple, Optional
import statistics
import logging

from .models import (
    Ishchi, Qiymetlendirme, Cavab, QiymetlendirmeDovru,
    Notification, QuickFeedback, InkishafPlani
)

logger = logging.getLogger('audit')


class AIRiskDetector:
    """
    AI əsaslı risk aşkarlama sistemi.
    Proaktiv olaraq problemli işçi münasibətlərini və riskləri aşkarlayır.
    """
    
    def __init__(self):
        self.red_flag_threshold = 3  # Qırmızı bayraq üçün minimum risklər
        self.low_performance_threshold = 3.0  # 10 üzərindən aşağı performans
        self.high_variance_threshold = 2.5  # Yüksək variant
        
    def analyze_employee_risks(self, employee: Ishchi, cycle: QiymetlendirmeDovru = None) -> Dict:
        """
        Bir işçi üçün bütün risk analizlərini aparır.
        """
        if not cycle:
            cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
            
        if not cycle:
            return {"error": "Aktiv qiymətləndirmə dövrü tapılmadı"}
        
        risks = {
            "employee_id": employee.id,
            "employee_name": employee.get_full_name(),
            "analysis_date": timezone.now(),
            "cycle": cycle.ad,
            "total_risk_score": 0,
            "risk_level": "LOW",
            "red_flags": [],
            "detailed_analysis": {}
        }
        
        # Müxtəlif risk analizləri
        performance_risk = self._analyze_performance_risk(employee, cycle)
        consistency_risk = self._analyze_consistency_risk(employee, cycle)
        peer_feedback_risk = self._analyze_peer_feedback_risk(employee, cycle)
        behavioral_risk = self._analyze_behavioral_risk(employee)
        
        # Risk nəticələrini birləşdir
        risks["detailed_analysis"] = {
            "performance_risk": performance_risk,
            "consistency_risk": consistency_risk,
            "peer_feedback_risk": peer_feedback_risk,
            "behavioral_risk": behavioral_risk
        }
        
        # Ümumi risk hesabla
        total_score = (
            performance_risk.get("risk_score", 0) +
            consistency_risk.get("risk_score", 0) +
            peer_feedback_risk.get("risk_score", 0) +
            behavioral_risk.get("risk_score", 0)
        )
        
        risks["total_risk_score"] = total_score
        risks["risk_level"] = self._calculate_risk_level(total_score)
        
        # Qırmızı bayraqlari topla
        for analysis in risks["detailed_analysis"].values():
            if analysis.get("red_flags"):
                risks["red_flags"].extend(analysis["red_flags"])
        
        # Risk bildirişi yarat
        if risks["risk_level"] in ["HIGH", "CRITICAL"]:
            self._create_risk_notification(employee, risks)
        
        return risks
    
    def _analyze_performance_risk(self, employee: Ishchi, cycle: QiymetlendirmeDovru) -> Dict:
        """
        Performans əsaslı risk analizi.
        """
        evaluations = Qiymetlendirme.objects.filter(
            qiymetlendirilen=employee,
            dovr=cycle,
            status='COMPLETED'
        )
        
        if not evaluations.exists():
            return {
                "risk_score": 1,
                "analysis": "Qiymətləndirmə məlumatı tapılmadı",
                "red_flags": ["NO_EVALUATION_DATA"]
            }
        
        # Ortalama bal hesabla
        total_scores = []
        for evaluation in evaluations:
            cavablar = evaluation.cavablar.all()
            if cavablar:
                avg_score = cavablar.aggregate(avg=Avg('xal'))['avg']
                if avg_score:
                    total_scores.append(avg_score)
        
        if not total_scores:
            return {
                "risk_score": 2,
                "analysis": "Cavab məlumatı tapılmadı",
                "red_flags": ["NO_ANSWER_DATA"]
            }
        
        average_performance = statistics.mean(total_scores)
        red_flags = []
        risk_score = 0
        
        # Aşağı performans yoxla
        if average_performance < self.low_performance_threshold:
            risk_score += 3
            red_flags.append("LOW_PERFORMANCE")
        
        # Çox az qiymətləndirici
        if evaluations.count() < 2:
            risk_score += 2
            red_flags.append("INSUFFICIENT_EVALUATORS")
        
        return {
            "risk_score": risk_score,
            "average_performance": round(average_performance, 2),
            "evaluation_count": evaluations.count(),
            "analysis": f"Ortalama performans: {average_performance:.2f}/10",
            "red_flags": red_flags
        }
    
    def _analyze_consistency_risk(self, employee: Ishchi, cycle: QiymetlendirmeDovru) -> Dict:
        """
        Qiymətləndirmə uyğunsuzluğu analizi.
        """
        evaluations = Qiymetlendirme.objects.filter(
            qiymetlendirilen=employee,
            dovr=cycle,
            status='COMPLETED'
        )
        
        if evaluations.count() < 2:
            return {
                "risk_score": 0,
                "analysis": "Uyğunsuzluq analizi üçün kifayət qədər məlumat yox",
                "red_flags": []
            }
        
        # Hər kateqoriya üçün balları topla
        category_scores = {}
        for evaluation in evaluations:
            for cavab in evaluation.cavablar.all():
                category = cavab.sual.kateqoriya.ad if cavab.sual.kateqoriya else "Ümumi"
                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(cavab.xal)
        
        red_flags = []
        risk_score = 0
        high_variance_categories = []
        
        for category, scores in category_scores.items():
            if len(scores) >= 2:
                variance = statistics.stdev(scores)
                if variance > self.high_variance_threshold:
                    high_variance_categories.append({
                        "category": category,
                        "variance": round(variance, 2),
                        "scores": scores
                    })
                    risk_score += 2
        
        if high_variance_categories:
            red_flags.append("HIGH_SCORE_VARIANCE")
        
        return {
            "risk_score": risk_score,
            "high_variance_categories": high_variance_categories,
            "analysis": f"{len(high_variance_categories)} kateqoriyada yüksək uyğunsuzluq",
            "red_flags": red_flags
        }
    
    def _analyze_peer_feedback_risk(self, employee: Ishchi, cycle: QiymetlendirmeDovru) -> Dict:
        """
        Həmkarlardan gələn rəy analizi.
        """
        # Son 30 gün ərzində aldığı sürətli rəylər
        thirty_days_ago = timezone.now() - timedelta(days=30)
        quick_feedback = QuickFeedback.objects.filter(
            to_user=employee,
            created_at__gte=thirty_days_ago
        )
        
        red_flags = []
        risk_score = 0
        
        # Neqativ rəy nisbəti
        total_feedback = quick_feedback.count()
        if total_feedback > 0:
            # Neqativ feedback (rating < 3 və ya müəyyən keyword-lər)
            negative_feedback = quick_feedback.filter(
                Q(rating__lt=3) |
                Q(message__icontains="problem") |
                Q(message__icontains="zəif") |
                Q(message__icontains="pis")
            ).count()
            
            negative_ratio = negative_feedback / total_feedback
            
            if negative_ratio > 0.6:  # 60%-dən çox neqativ
                risk_score += 3
                red_flags.append("HIGH_NEGATIVE_FEEDBACK")
            elif negative_ratio > 0.4:  # 40%-dən çox neqativ
                risk_score += 1
        
        # Çox az feedback
        if total_feedback < 2:
            risk_score += 1
            red_flags.append("LOW_PEER_INTERACTION")
        
        return {
            "risk_score": risk_score,
            "total_feedback": total_feedback,
            "negative_ratio": round(negative_feedback / max(total_feedback, 1), 2),
            "analysis": f"{total_feedback} rəy, {negative_feedback} neqativ",
            "red_flags": red_flags
        }
    
    def _analyze_behavioral_risk(self, employee: Ishchi) -> Dict:
        """
        Davranış əsaslı risk analizi.
        """
        red_flags = []
        risk_score = 0
        
        # Son login aktivliyi
        if employee.last_login:
            days_since_login = (timezone.now().date() - employee.last_login.date()).days
            if days_since_login > 14:
                risk_score += 2
                red_flags.append("LONG_ABSENCE")
        
        # İnkişaf planı aktivliyi
        active_plans = InkishafPlani.objects.filter(
            ishchi=employee,
            status=InkishafPlani.Status.AKTIV
        ).count()
        
        if active_plans == 0:
            risk_score += 1
            red_flags.append("NO_DEVELOPMENT_PLAN")
        
        # Təşkilati uyğunsuzluq
        if not employee.organization_unit:
            risk_score += 1
            red_flags.append("NO_ORGANIZATIONAL_UNIT")
        
        return {
            "risk_score": risk_score,
            "days_since_login": (timezone.now().date() - employee.last_login.date()).days if employee.last_login else None,
            "active_development_plans": active_plans,
            "analysis": f"Davranış risk səviyyəsi: {risk_score}",
            "red_flags": red_flags
        }
    
    def _calculate_risk_level(self, total_score: int) -> str:
        """
        Ümumi risk səviyyəsini hesabla.
        """
        if total_score >= 10:
            return "CRITICAL"
        elif total_score >= 6:
            return "HIGH"
        elif total_score >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _create_risk_notification(self, employee: Ishchi, risk_data: Dict):
        """
        Yüksək risk üçün bildiriş yarat.
        """
        # HR və rəhbərlərə bildiriş göndər
        hr_users = Ishchi.objects.filter(rol__in=['ADMIN', 'SUPERADMIN'])
        
        title = f"⚠️ Yüksək Risk: {employee.get_full_name()}"
        message = f"""
        İşçi: {employee.get_full_name()}
        Risk Səviyyəsi: {risk_data['risk_level']}
        Risk Xalı: {risk_data['total_risk_score']}
        
        Qırmızı Bayraqllar:
        {', '.join(risk_data['red_flags'])}
        
        Təcili diqqət tələb olunur.
        """
        
        for hr_user in hr_users:
            Notification.objects.create(
                recipient=hr_user,
                title=title,
                message=message,
                notification_type=Notification.NotificationType.WARNING,
                priority=Notification.Priority.HIGH,
                action_text="Detallara bax",
                action_url=f"/core/employees/{employee.id}/risk-analysis/"
            )
        
        # Audit log
        logger.info(
            "AI Risk Detection Alert",
            extra={
                "user": "AI_SYSTEM",
                "action_type": "RISK_DETECTED",
                "object_type": "EMPLOYEE_RISK",
                "object_id": employee.id,
                "details": {
                    "employee": employee.get_full_name(),
                    "risk_level": risk_data['risk_level'],
                    "risk_score": risk_data['total_risk_score'],
                    "red_flags": risk_data['red_flags']
                }
            }
        )
    
    def bulk_analyze_all_employees(self, cycle: QiymetlendirmeDovru = None) -> List[Dict]:
        """
        Bütün aktiv işçilər üçün risk analizi.
        """
        if not cycle:
            cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        
        if not cycle:
            return []
        
        employees = Ishchi.objects.filter(is_active=True, rol='ISHCHI')
        results = []
        
        for employee in employees:
            try:
                risk_data = self.analyze_employee_risks(employee, cycle)
                results.append(risk_data)
            except Exception as e:
                logger.error(
                    f"Risk analizi xətası: {employee.get_full_name()}",
                    extra={"error": str(e)}
                )
        
        # Nəticələri risk səviyyəsinə görə sırala
        results.sort(key=lambda x: x.get('total_risk_score', 0), reverse=True)
        
        return results
    
    def get_organization_risk_summary(self) -> Dict:
        """
        Təşkilat üçün ümumi risk xülasəsi.
        """
        all_risks = self.bulk_analyze_all_employees()
        
        risk_levels = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        red_flag_counts = {}
        
        for risk in all_risks:
            risk_levels[risk.get('risk_level', 'LOW')] += 1
            
            for flag in risk.get('red_flags', []):
                red_flag_counts[flag] = red_flag_counts.get(flag, 0) + 1
        
        return {
            "total_employees_analyzed": len(all_risks),
            "risk_distribution": risk_levels,
            "top_red_flags": sorted(red_flag_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "analysis_date": timezone.now(),
            "critical_employees": [r for r in all_risks if r.get('risk_level') == 'CRITICAL']
        }