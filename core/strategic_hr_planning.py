# core/strategic_hr_planning.py

import numpy as np
import pandas as pd
from django.db.models import Avg, Count, Q, Sum, StdDev
from django.utils import timezone
from datetime import timedelta, date
from typing import Dict, List, Tuple, Optional
import logging

from .models import (
    Ishchi, Qiymetlendirme, Cavab, QiymetlendirmeDovru,
    OrganizationUnit, InkishafPlani, RiskFlag, EmployeeRiskAnalysis,
    PsychologicalRiskResponse
)

logger = logging.getLogger('audit')


class StrategicHRPlanner:
    """
    Strateji kadr planlaşdırması sistemi.
    İşçi potensialını qiymətləndirir, varislik planlaması aparır,
    talent pipeline idarə edir və HR strategiyası üçün tövsiyələr verir.
    """
    
    def __init__(self):
        self.performance_threshold = 4.0  # Yüksək performans hədd
        self.high_potential_threshold = 4.5  # Yüksək potensial hədd
        self.retention_risk_threshold = 3.0  # Saxlama riski hədd
    
    def analyze_workforce_composition(self, organization_unit: OrganizationUnit = None) -> Dict:
        """
        İş qüvvəsi tərkibini analiz edir
        """
        employees_query = Ishchi.objects.filter(is_active=True, rol='ISHCHI')
        
        if organization_unit:
            employees_query = employees_query.filter(
                Q(organization_unit=organization_unit) |
                Q(organization_unit__parent=organization_unit)
            )
        
        employees = employees_query
        total_count = employees.count()
        
        if total_count == 0:
            return {"error": "İşçi tapılmadı"}
        
        # Yaş demografiyası
        current_year = timezone.now().year
        age_distribution = {}
        age_ranges = [
            (20, 30, "20-30"),
            (31, 40, "31-40"),
            (41, 50, "41-50"),
            (51, 65, "51-65")
        ]
        
        for min_age, max_age, label in age_ranges:
            count = employees.filter(
                dogum_tarixi__year__lte=current_year - min_age,
                dogum_tarixi__year__gte=current_year - max_age
            ).count()
            
            age_distribution[label] = {
                'count': count,
                'percentage': round((count / total_count) * 100, 1)
            }
        
        # Təşkilati vahid üzrə paylanma
        unit_distribution = employees.values(
            'organization_unit__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Vəzifə səviyyəsi paylanması
        position_levels = {
            'senior': ['Senior', 'Baş', 'Rəhbər', 'Direktor'],
            'middle': ['Mütəxəssis', 'Aparıcı', 'Koordinator'],
            'junior': ['Kiçik', 'Yardımçı', 'Stajçı']
        }
        
        position_distribution = {}
        for level, keywords in position_levels.items():
            count = 0
            for keyword in keywords:
                count += employees.filter(vezife__icontains=keyword).count()
            
            position_distribution[level] = {
                'count': count,
                'percentage': round((count / total_count) * 100, 1)
            }
        
        # İş təcrübəsi (işə başlama tarixi əsasında)
        experience_distribution = {}
        experience_ranges = [
            (0, 1, "0-1 il"),
            (1, 3, "1-3 il"),
            (3, 5, "3-5 il"),
            (5, 10, "5-10 il"),
            (10, 100, "10+ il")
        ]
        
        for min_exp, max_exp, label in experience_ranges:
            start_date = timezone.now() - timedelta(days=max_exp*365)
            end_date = timezone.now() - timedelta(days=min_exp*365)
            
            count = employees.filter(
                date_joined__gte=start_date,
                date_joined__lte=end_date
            ).count()
            
            experience_distribution[label] = {
                'count': count,
                'percentage': round((count / total_count) * 100, 1)
            }
        
        return {
            'total_employees': total_count,
            'analysis_date': timezone.now(),
            'organization_unit': organization_unit.name if organization_unit else 'Bütün təşkilat',
            'demographics': {
                'age_distribution': age_distribution,
                'experience_distribution': experience_distribution,
                'position_distribution': position_distribution
            },
            'unit_distribution': list(unit_distribution),
            'insights': self._generate_workforce_insights(
                age_distribution, experience_distribution, position_distribution
            )
        }
    
    def identify_high_potential_employees(self, cycle: QiymetlendirmeDovru = None) -> Dict:
        """
        Yüksək potensial işçiləri müəyyən edir (9-box grid)
        """
        if not cycle:
            cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        
        if not cycle:
            return {"error": "Aktiv dövr tapılmadı"}
        
        high_potential_employees = []
        employees = Ishchi.objects.filter(is_active=True, rol='ISHCHI')
        
        for employee in employees:
            # Performans xalı
            evaluations = Qiymetlendirme.objects.filter(
                qiymetlendirilen=employee,
                dovr=cycle,
                status='COMPLETED'
            )
            
            if not evaluations.exists():
                continue
                
            performance_scores = []
            for evaluation in evaluations:
                cavablar = evaluation.cavablar.all()
                if cavablar:
                    avg_score = cavablar.aggregate(avg=Avg('xal'))['avg']
                    if avg_score:
                        performance_scores.append(avg_score)
            
            if not performance_scores:
                continue
                
            avg_performance = np.mean(performance_scores)
            
            # Potensial qiymətləndirməsi (inkişaf planları, feedback, risk analizi əsasında)
            potential_score = self._calculate_potential_score(employee, cycle)
            
            # 9-box grid yerləşdirmə
            grid_position = self._determine_9box_position(avg_performance, potential_score)
            
            # Risk qiymətləndirməsi
            retention_risk = self._assess_retention_risk(employee, cycle)
            
            employee_data = {
                'employee_id': employee.id,
                'employee_name': employee.get_full_name(),
                'position': employee.vezife,
                'unit': employee.organization_unit.name if employee.organization_unit else 'N/A',
                'performance_score': round(avg_performance, 2),
                'potential_score': round(potential_score, 2),
                'grid_position': grid_position,
                'retention_risk': retention_risk,
                'is_high_potential': grid_position in ['high_potential', 'future_leader', 'star'],
                'succession_ready': grid_position in ['future_leader', 'star'] and retention_risk < 3
            }
            
            high_potential_employees.append(employee_data)
        
        # Potensial və performansa görə sırala
        high_potential_employees.sort(
            key=lambda x: (x['potential_score'], x['performance_score']), 
            reverse=True
        )
        
        # Grid pozisiyalarına görə qruplaşdır
        grid_summary = {}
        for emp in high_potential_employees:
            position = emp['grid_position']
            if position not in grid_summary:
                grid_summary[position] = {'count': 0, 'employees': []}
            grid_summary[position]['count'] += 1
            grid_summary[position]['employees'].append(emp)
        
        return {
            'cycle': cycle.ad,
            'total_analyzed': len(high_potential_employees),
            'high_potential_count': len([e for e in high_potential_employees if e['is_high_potential']]),
            'succession_ready_count': len([e for e in high_potential_employees if e['succession_ready']]),
            'grid_summary': grid_summary,
            'top_talents': high_potential_employees[:20],  # Top 20
            'analysis_date': timezone.now()
        }
    
    def create_succession_plan(self, organization_unit: OrganizationUnit = None) -> Dict:
        """
        Varislik planı yaradır
        """
        # Açıq və ya kritik vəzifələri müəyyən et
        key_positions = self._identify_key_positions(organization_unit)
        
        succession_plans = []
        
        for position_data in key_positions:
            position = position_data['position']
            unit = position_data['unit']
            current_incumbent = position_data.get('current_incumbent')
            
            # Bu vəzifə üçün uyğun namizədləri tap
            candidates = self._find_succession_candidates(position, unit)
            
            succession_plan = {
                'position': position,
                'unit': unit,
                'current_incumbent': current_incumbent,
                'readiness_level': position_data.get('readiness_level', 'medium'),
                'candidates': candidates[:5],  # Top 5 namizəd
                'development_needs': self._identify_development_needs(candidates),
                'timeline': self._estimate_succession_timeline(candidates)
            }
            
            succession_plans.append(succession_plan)
        
        return {
            'organization_unit': organization_unit.name if organization_unit else 'Bütün təşkilat',
            'total_key_positions': len(key_positions),
            'succession_plans': succession_plans,
            'summary': {
                'ready_now': len([p for p in succession_plans if p['timeline'] == 'ready_now']),
                'ready_1_year': len([p for p in succession_plans if p['timeline'] == '1_year']),
                'ready_2_3_years': len([p for p in succession_plans if p['timeline'] == '2_3_years']),
                'needs_development': len([p for p in succession_plans if p['timeline'] == 'needs_development'])
            },
            'generated_at': timezone.now()
        }
    
    def analyze_talent_pipeline(self) -> Dict:
        """
        Talent pipeline analizi
        """
        cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        if not cycle:
            return {"error": "Aktiv dövr tapılmadı"}
        
        # Performans və potensial əsasında talent kategoriyaları
        talent_categories = {
            'stars': [],           # Yüksək performans + Yüksək potensial
            'high_performers': [], # Yüksək performans + Orta potensial
            'high_potentials': [], # Orta performans + Yüksək potensial
            'solid_performers': [],# Orta performans + Orta potensial
            'underperformers': [] # Aşağı performans
        }
        
        employees = Ishchi.objects.filter(is_active=True, rol='ISHCHI')
        
        for employee in employees:
            performance_data = self._get_employee_performance(employee, cycle)
            if not performance_data:
                continue
                
            performance = performance_data['performance']
            potential = self._calculate_potential_score(employee, cycle)
            
            # Kateqoriya təyin etmə
            if performance >= 4.5 and potential >= 4.5:
                talent_categories['stars'].append({
                    'employee': employee,
                    'performance': performance,
                    'potential': potential
                })
            elif performance >= 4.0 and potential < 4.5:
                talent_categories['high_performers'].append({
                    'employee': employee,
                    'performance': performance,
                    'potential': potential
                })
            elif performance < 4.0 and potential >= 4.0:
                talent_categories['high_potentials'].append({
                    'employee': employee,
                    'performance': performance,
                    'potential': potential
                })
            elif performance >= 3.0 and potential >= 3.0:
                talent_categories['solid_performers'].append({
                    'employee': employee,
                    'performance': performance,
                    'potential': potential
                })
            else:
                talent_categories['underperformers'].append({
                    'employee': employee,
                    'performance': performance,
                    'potential': potential
                })
        
        # Hər kateqoriya üçün statistika
        pipeline_summary = {}
        for category, employees_list in talent_categories.items():
            pipeline_summary[category] = {
                'count': len(employees_list),
                'percentage': round((len(employees_list) / employees.count()) * 100, 1),
                'employees': [
                    {
                        'id': emp['employee'].id,
                        'name': emp['employee'].get_full_name(),
                        'position': emp['employee'].vezife,
                        'unit': emp['employee'].organization_unit.name if emp['employee'].organization_unit else 'N/A',
                        'performance': round(emp['performance'], 2),
                        'potential': round(emp['potential'], 2)
                    } for emp in employees_list[:10]  # Top 10
                ]
            }
        
        # Talent flow analizi
        talent_flow = self._analyze_talent_flow()
        
        return {
            'cycle': cycle.ad,
            'total_employees': employees.count(),
            'pipeline_summary': pipeline_summary,
            'talent_flow': talent_flow,
            'recommendations': self._generate_talent_recommendations(pipeline_summary),
            'analysis_date': timezone.now()
        }
    
    def generate_hr_strategy_recommendations(self, organization_unit: OrganizationUnit = None) -> Dict:
        """
        HR strategiyası üçün tövsiyələr yaradır
        """
        # Müxtəlif analizləri birləşdir
        workforce_analysis = self.analyze_workforce_composition(organization_unit)
        talent_analysis = self.analyze_talent_pipeline()
        high_potential_analysis = self.identify_high_potential_employees()
        
        # Risk analizi
        active_cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        risk_summary = self._analyze_organizational_risks(active_cycle)
        
        recommendations = {
            'recruitment_strategy': self._generate_recruitment_recommendations(workforce_analysis, talent_analysis),
            'development_strategy': self._generate_development_recommendations(high_potential_analysis, talent_analysis),
            'retention_strategy': self._generate_retention_recommendations(risk_summary),
            'succession_strategy': self._generate_succession_recommendations(high_potential_analysis),
            'diversity_inclusion': self._generate_diversity_recommendations(workforce_analysis),
            'performance_management': self._generate_performance_recommendations(talent_analysis)
        }
        
        # Prioritet matrisi
        priority_matrix = self._create_priority_matrix(recommendations)
        
        return {
            'organization_unit': organization_unit.name if organization_unit else 'Bütün təşkilat',
            'recommendations': recommendations,
            'priority_matrix': priority_matrix,
            'key_metrics': {
                'total_employees': workforce_analysis.get('total_employees', 0),
                'high_potential_percentage': round(
                    (high_potential_analysis.get('high_potential_count', 0) / max(workforce_analysis.get('total_employees', 1), 1)) * 100, 1
                ),
                'succession_readiness': high_potential_analysis.get('succession_ready_count', 0),
                'retention_risk_employees': risk_summary.get('high_risk_employees', 0)
            },
            'generated_at': timezone.now()
        }
    
    def _calculate_potential_score(self, employee: Ishchi, cycle: QiymetlendirmeDovru) -> float:
        """
        İşçinin potensial xalını hesablayır
        """
        potential_factors = []
        
        # İnkişaf planı aktivliyi (25%)
        active_plans = InkishafPlani.objects.filter(
            ishchi=employee,
            status=InkishafPlani.Status.AKTIV
        ).count()
        
        development_score = min(active_plans * 2, 5)  # Max 5
        potential_factors.append(development_score * 0.25)
        
        # Liderlik potensiali - feedback analizi (30%)
        from .models import QuickFeedback
        positive_feedback = QuickFeedback.objects.filter(
            to_user=employee,
            rating__gte=4,
            created_at__gte=timezone.now() - timedelta(days=90)
        ).count()
        
        leadership_score = min(positive_feedback * 0.5, 5)  # Max 5
        potential_factors.append(leadership_score * 0.3)
        
        # Məhsuldarlıq trendi (25%)
        performance_trend = self._calculate_performance_trend(employee)
        potential_factors.append(performance_trend * 0.25)
        
        # Risk səviyyəsi (ters mütənasib) (20%)
        risk_analysis = EmployeeRiskAnalysis.objects.filter(
            employee=employee,
            cycle=cycle
        ).first()
        
        risk_score = 5  # Default yüksək potensial
        if risk_analysis:
            risk_levels = {'LOW': 5, 'MEDIUM': 4, 'HIGH': 2, 'CRITICAL': 1}
            risk_score = risk_levels.get(risk_analysis.risk_level, 3)
        
        potential_factors.append(risk_score * 0.2)
        
        return sum(potential_factors)
    
    def _determine_9box_position(self, performance: float, potential: float) -> str:
        """
        9-box grid üzrə mövqe təyin edir
        """
        if performance >= 4.5 and potential >= 4.5:
            return 'star'
        elif performance >= 4.0 and potential >= 4.5:
            return 'future_leader'
        elif performance >= 4.5 and potential >= 3.5:
            return 'current_leader'
        elif performance >= 4.0 and potential >= 3.5:
            return 'high_potential'
        elif performance >= 3.5 and potential >= 4.0:
            return 'emerging_talent'
        elif performance >= 3.5 and potential >= 3.0:
            return 'solid_performer'
        elif performance >= 3.0 and potential >= 3.5:
            return 'developing'
        elif performance >= 3.0 and potential >= 2.5:
            return 'inconsistent'
        else:
            return 'underperformer'
    
    def _assess_retention_risk(self, employee: Ishchi, cycle: QiymetlendirmeDovru) -> float:
        """
        İşçinin saxlama riskini qiymətləndirir (1-5 skala)
        """
        risk_factors = []
        
        # Performans məmnunluğu
        performance = self._get_employee_performance(employee, cycle)
        if performance and performance['performance'] < 3.5:
            risk_factors.append(2)  # Aşağı performans riski
        
        # Psixoloji risk sorğuları
        psych_responses = PsychologicalRiskResponse.objects.filter(
            employee=employee,
            requires_attention=True
        )
        
        if psych_responses.exists():
            risk_factors.append(1.5)
        
        # Risk bayraqlari
        active_flags = RiskFlag.objects.filter(
            employee=employee,
            cycle=cycle,
            status=RiskFlag.Status.ACTIVE
        ).count()
        
        if active_flags > 2:
            risk_factors.append(1)
        
        # Son aktivlik
        if employee.last_login:
            days_since_login = (timezone.now().date() - employee.last_login.date()).days
            if days_since_login > 7:
                risk_factors.append(0.5)
        
        return min(sum(risk_factors), 5)
    
    def _get_employee_performance(self, employee: Ishchi, cycle: QiymetlendirmeDovru) -> Optional[Dict]:
        """
        İşçinin performans məlumatlarını alır
        """
        evaluations = Qiymetlendirme.objects.filter(
            qiymetlendirilen=employee,
            dovr=cycle,
            status='COMPLETED'
        )
        
        if not evaluations.exists():
            return None
            
        scores = []
        for evaluation in evaluations:
            cavablar = evaluation.cavablar.all()
            if cavablar:
                avg_score = cavablar.aggregate(avg=Avg('xal'))['avg']
                if avg_score:
                    scores.append(avg_score)
        
        if not scores:
            return None
            
        return {
            'performance': np.mean(scores),
            'consistency': np.std(scores) if len(scores) > 1 else 0,
            'evaluation_count': len(scores)
        }
    
    def _calculate_performance_trend(self, employee: Ishchi) -> float:
        """
        Performans trendini hesablayır
        """
        # Son 3 dövrün performansını müqayisə et
        recent_cycles = QiymetlendirmeDovru.objects.order_by('-bashlama_tarixi')[:3]
        
        performance_history = []
        for cycle in recent_cycles:
            perf_data = self._get_employee_performance(employee, cycle)
            if perf_data:
                performance_history.append(perf_data['performance'])
        
        if len(performance_history) < 2:
            return 3.0  # Neytrall
        
        # Linear trend hesabla
        x = list(range(len(performance_history)))
        y = performance_history
        
        if len(x) >= 2:
            slope = np.polyfit(x, y, 1)[0]
            # Slope-u 1-5 skalasına çevir
            trend_score = 3 + (slope * 2)  # Normalize et
            return max(1, min(5, trend_score))
        
        return 3.0
    
    def _identify_key_positions(self, organization_unit: OrganizationUnit = None) -> List[Dict]:
        """
        Açar vəzifələri müəyyən edir
        """
        # Bu sadələşdirilmiş versiyadadır - real həyatda daha mürəkkəb məntiqlər ola bilər
        key_positions = []
        
        employees_query = Ishchi.objects.filter(is_active=True, rol__in=['REHBER', 'ADMIN'])
        
        if organization_unit:
            employees_query = employees_query.filter(organization_unit=organization_unit)
        
        for employee in employees_query:
            # Rəhbər vəzifələri əsasən açar sayılır
            key_positions.append({
                'position': employee.vezife,
                'unit': employee.organization_unit.name if employee.organization_unit else 'N/A',
                'current_incumbent': {
                    'id': employee.id,
                    'name': employee.get_full_name(),
                    'tenure': (timezone.now().date() - employee.date_joined.date()).days // 365
                },
                'readiness_level': 'high' if employee.rol == 'ADMIN' else 'medium'
            })
        
        return key_positions
    
    def _find_succession_candidates(self, position: str, unit: str) -> List[Dict]:
        """
        Varislik namizədlərini tapır
        """
        # Yüksək potensial işçiləri namizəd kimi götür
        candidates = []
        
        employees = Ishchi.objects.filter(
            is_active=True,
            rol='ISHCHI'
        )
        
        # Eyni və ya əlaqəli vahiddən namizədlər
        if unit != 'N/A':
            try:
                org_unit = OrganizationUnit.objects.get(name=unit)
                employees = employees.filter(
                    Q(organization_unit=org_unit) |
                    Q(organization_unit__parent=org_unit)
                )
            except OrganizationUnit.DoesNotExist:
                pass
        
        cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        if not cycle:
            return []
        
        for employee in employees:
            performance_data = self._get_employee_performance(employee, cycle)
            if not performance_data:
                continue
                
            potential_score = self._calculate_potential_score(employee, cycle)
            
            # Yalnız yüksək potensialı olanları daxil et
            if potential_score >= 3.5:
                candidates.append({
                    'employee_id': employee.id,
                    'name': employee.get_full_name(),
                    'current_position': employee.vezife,
                    'performance': round(performance_data['performance'], 2),
                    'potential': round(potential_score, 2),
                    'readiness': self._assess_succession_readiness(employee, position)
                })
        
        # Potensial və hazırlığa görə sırala
        candidates.sort(key=lambda x: (x['potential'], x['readiness']), reverse=True)
        
        return candidates
    
    def _assess_succession_readiness(self, employee: Ishchi, target_position: str) -> str:
        """
        Varislik hazırlığını qiymətləndirir
        """
        # Bu sadə versiyadadır - real həyatda skills assessment, competency mapping olardı
        performance_data = self._get_employee_performance(
            employee, 
            QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        )
        
        if not performance_data:
            return 'needs_development'
        
        performance = performance_data['performance']
        potential = self._calculate_potential_score(
            employee,
            QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        )
        
        if performance >= 4.5 and potential >= 4.5:
            return 'ready_now'
        elif performance >= 4.0 and potential >= 4.0:
            return '1_year'
        elif performance >= 3.5 and potential >= 3.5:
            return '2_3_years'
        else:
            return 'needs_development'
    
    def _identify_development_needs(self, candidates: List[Dict]) -> List[str]:
        """
        İnkişaf ehtiyaclarını müəyyən edir
        """
        common_needs = [
            'Liderlik bacarıqları',
            'Strateji düşünmə',
            'Komanda idarəçiliği',
            'Kommunikasiya bacarıqları',
            'Qərar qəbuletmə',
            'Dəyişikliklərə uyğunlaşma'
        ]
        
        # Real versiyada competency gap analysis olardı
        return common_needs[:4]  # İlk 4 prioritet
    
    def _estimate_succession_timeline(self, candidates: List[Dict]) -> str:
        """
        Varislik vaxt çərçivəsini təxmin edir
        """
        if not candidates:
            return 'needs_development'
        
        best_candidate = candidates[0]
        return best_candidate.get('readiness', 'needs_development')
    
    def _analyze_talent_flow(self) -> Dict:
        """
        Talent axını analiz edir
        """
        # Bu versiyada sadələşdirilmiş - real həyatda historical data lazımdır
        return {
            'internal_promotion_rate': 75,  # %
            'external_hire_rate': 25,       # %
            'retention_rate': 85,           # %
            'time_to_fill': 45              # gün
        }
    
    def _generate_talent_recommendations(self, pipeline_summary: Dict) -> List[str]:
        """
        Talent pipeline əsasında tövsiyələr yaradır
        """
        recommendations = []
        
        stars_count = pipeline_summary.get('stars', {}).get('count', 0)
        high_potentials_count = pipeline_summary.get('high_potentials', {}).get('count', 0)
        underperformers_count = pipeline_summary.get('underperformers', {}).get('count', 0)
        
        if stars_count < 5:
            recommendations.append("Star talent sayını artırmaq üçün high potential işçilərin inkişafına diqqət yetirin")
        
        if high_potentials_count > stars_count * 2:
            recommendations.append("High potential işçilərin performansını artırmaq üçün mentoring proqramları yaradın")
        
        if underperformers_count > 10:
            recommendations.append("Underperformer işçilər üçün Performance Improvement Plan həyata keçirin")
        
        return recommendations
    
    def _analyze_organizational_risks(self, cycle: QiymetlendirmeDovru) -> Dict:
        """
        Təşkilati riskləri analiz edir
        """
        if not cycle:
            return {'high_risk_employees': 0, 'critical_positions_at_risk': 0}
        
        high_risk_employees = EmployeeRiskAnalysis.objects.filter(
            cycle=cycle,
            risk_level__in=['HIGH', 'CRITICAL']
        ).count()
        
        critical_flags = RiskFlag.objects.filter(
            cycle=cycle,
            severity=RiskFlag.Severity.CRITICAL,
            status=RiskFlag.Status.ACTIVE
        ).count()
        
        return {
            'high_risk_employees': high_risk_employees,
            'critical_positions_at_risk': critical_flags,
            'retention_alerts': high_risk_employees
        }
    
    def _generate_workforce_insights(self, age_dist: Dict, exp_dist: Dict, pos_dist: Dict) -> List[str]:
        """
        İş qüvvəsi təhlili üçün insights yaradır
        """
        insights = []
        
        # Yaş analizi
        young_percentage = age_dist.get('20-30', {}).get('percentage', 0)
        if young_percentage < 20:
            insights.append("Gənc talent cəlb etməyə ehtiyac var")
        
        senior_percentage = age_dist.get('51-65', {}).get('percentage', 0)
        if senior_percentage > 30:
            insights.append("Yaşlı işçilərin biliyini transfer etməyə fokus lazımdır")
        
        # Təcrübə analizi
        new_hires = exp_dist.get('0-1 il', {}).get('percentage', 0)
        if new_hires > 25:
            insights.append("Yeni işçilərin adaptasiyası üçün onboarding proqramlarını gücləndin")
        
        return insights
    
    def _generate_recruitment_recommendations(self, workforce: Dict, talent: Dict) -> List[str]:
        """
        İşe qəbul strategiyası tövsiyələri
        """
        recommendations = []
        
        total_employees = workforce.get('total_employees', 0)
        stars_count = talent.get('pipeline_summary', {}).get('stars', {}).get('count', 0)
        
        if stars_count / max(total_employees, 1) < 0.05:  # 5%-dən az star
            recommendations.append("Senior level talent cəlb etməyə fokus edin")
        
        recommendations.append("Referral proqramlarını gücləndirin")
        recommendations.append("Employer branding strategiyasını inkişaf etdirin")
        
        return recommendations
    
    def _generate_development_recommendations(self, high_potential: Dict, talent: Dict) -> List[str]:
        """
        İnkişaf strategiyası tövsiyələri
        """
        recommendations = []
        
        high_potential_count = high_potential.get('high_potential_count', 0)
        succession_ready = high_potential.get('succession_ready_count', 0)
        
        if succession_ready < high_potential_count * 0.3:
            recommendations.append("Succession planning proqramlarını genişləndirin")
        
        recommendations.append("Leadership development proqramlarını yaradın")
        recommendations.append("Cross-functional project assignment-ləri artırın")
        recommendations.append("Mentoring və coaching proqramlarını həyata keçirin")
        
        return recommendations
    
    def _generate_retention_recommendations(self, risk_summary: Dict) -> List[str]:
        """
        Saxlama strategiyası tövsiyələri
        """
        recommendations = []
        
        high_risk_count = risk_summary.get('high_risk_employees', 0)
        
        if high_risk_count > 5:
            recommendations.append("High-risk işçilər üçün retention bonus proqramı düşünün")
            recommendations.append("Exit interview prosesini güclənirin")
        
        recommendations.append("Employee engagement sorğuları keçirin")
        recommendations.append("Career development path-ləri aydınlaşdırın")
        recommendations.append("Work-life balance inisiyativləri başladın")
        
        return recommendations
    
    def _generate_succession_recommendations(self, high_potential: Dict) -> List[str]:
        """
        Varislik strategiyası tövsiyələri
        """
        recommendations = []
        
        succession_ready = high_potential.get('succession_ready_count', 0)
        
        if succession_ready < 10:
            recommendations.append("Succession planning proqramını genişləndirin")
        
        recommendations.append("Key position-lar üçün backup planları yaradın")
        recommendations.append("Job rotation proqramlarını həyata keçirin")
        recommendations.append("Stretch assignment-lər verin")
        
        return recommendations
    
    def _generate_diversity_recommendations(self, workforce: Dict) -> List[str]:
        """
        Müxtəliflik və inklüzyon tövsiyələri
        """
        recommendations = []
        
        # Bu sadə versiyadadır - real həyatda gender, ethnicity analytics olardı
        recommendations.append("Diversity hiring initiatives başladın")
        recommendations.append("Inclusive leadership training həyata keçirin")
        recommendations.append("Employee Resource Groups yaradın")
        
        return recommendations
    
    def _generate_performance_recommendations(self, talent: Dict) -> List[str]:
        """
        Performans idarəetmə tövsiyələri
        """
        recommendations = []
        
        underperformers = talent.get('pipeline_summary', {}).get('underperformers', {}).get('count', 0)
        
        if underperformers > 10:
            recommendations.append("Performance improvement plan prosesini təkmilləşdirin")
        
        recommendations.append("Continuous feedback sistemini qurrun")
        recommendations.append("Goal-setting və tracking sistemlərini inkişaf etdirin")
        recommendations.append("Performance coaching proqramlarını başladın")
        
        return recommendations
    
    def _create_priority_matrix(self, recommendations: Dict) -> Dict:
        """
        Tövsiyələr üçün prioritet matrisi yaradır
        """
        priority_matrix = {
            'high_priority': [
                recommendations.get('retention_strategy', [])[:2],
                recommendations.get('succession_strategy', [])[:1]
            ],
            'medium_priority': [
                recommendations.get('development_strategy', [])[:2],
                recommendations.get('performance_management', [])[:2]
            ],
            'low_priority': [
                recommendations.get('diversity_inclusion', [])[:2],
                recommendations.get('recruitment_strategy', [])[:1]
            ]
        }
        
        # Flatten the lists
        for priority, rec_lists in priority_matrix.items():
            flattened = []
            for rec_list in rec_lists:
                flattened.extend(rec_list)
            priority_matrix[priority] = flattened
        
        return priority_matrix