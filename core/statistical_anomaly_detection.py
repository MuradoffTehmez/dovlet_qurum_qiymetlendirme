# core/statistical_anomaly_detection.py

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from django.db.models import Avg, StdDev, Count, Q
from django.utils import timezone
from datetime import timedelta, date
from typing import Dict, List, Tuple, Optional
import logging

from .models import (
    Ishchi, Qiymetlendirme, Cavab, QiymetlendirmeDovru,
    QuickFeedback, RiskFlag, EmployeeRiskAnalysis
)

logger = logging.getLogger('audit')


class StatisticalAnomalyDetector:
    """
    Statistik anormal davranış aşkarlama sistemi.
    Machine Learning və statistik metodlardan istifadə edərək 
    işçilərin davranışında anomaliyaları aşkarlayır.
    """
    
    def __init__(self):
        self.contamination = 0.1  # Anomaliy nisbəti (10%)
        self.std_threshold = 2.5  # Standard deviation threshold
        self.min_data_points = 5  # Minimum məlumat nöqtəsi
        
    def detect_performance_anomalies(self, cycle: QiymetlendirmeDovru = None) -> Dict:
        """
        Performans anomaliyalarını aşkarlayır
        """
        if not cycle:
            cycle = QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
        
        if not cycle:
            return {"error": "Aktiv dövr tapılmadı"}
        
        # Bütün işçilərin performans məlumatlarını toplayır
        performance_data = []
        employees = Ishchi.objects.filter(is_active=True, rol='ISHCHI')
        
        for employee in employees:
            evaluations = Qiymetlendirme.objects.filter(
                qiymetlendirilen=employee,
                dovr=cycle,
                status='COMPLETED'
            )
            
            if evaluations.exists():
                scores = []
                for evaluation in evaluations:
                    cavablar = evaluation.cavablar.all()
                    if cavablar:
                        avg_score = cavablar.aggregate(avg=Avg('xal'))['avg']
                        if avg_score:
                            scores.append(avg_score)
                
                if scores:
                    employee_avg = np.mean(scores)
                    employee_std = np.std(scores) if len(scores) > 1 else 0
                    
                    performance_data.append({
                        'employee_id': employee.id,
                        'employee_name': employee.get_full_name(),
                        'avg_score': employee_avg,
                        'std_score': employee_std,
                        'evaluation_count': len(scores),
                        'score_variance': np.var(scores) if len(scores) > 1 else 0
                    })
        
        if len(performance_data) < self.min_data_points:
            return {"error": "Kifayətsiz məlumat"}
        
        # DataFrame yaradır
        df = pd.DataFrame(performance_data)
        
        # Anomaliy aşkarlama metodları
        anomalies = {
            'statistical_outliers': self._detect_statistical_outliers(df),
            'isolation_forest': self._detect_isolation_forest_anomalies(df),
            'z_score_anomalies': self._detect_z_score_anomalies(df),
            'performance_clusters': self._detect_performance_clusters(df)
        }
        
        # Kombine edilmiş anomaliy nəticəsi
        combined_anomalies = self._combine_anomaly_results(anomalies, df)
        
        return {
            'cycle': cycle.ad,
            'total_employees': len(performance_data),
            'anomalies_detected': len(combined_anomalies),
            'detection_methods': anomalies,
            'combined_results': combined_anomalies,
            'analysis_date': timezone.now()
        }
    
    def detect_behavioral_anomalies(self, days_back: int = 30) -> Dict:
        """
        Davranış anomaliyalarını aşkarlayır (feedback patterns, login frequency, etc.)
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)
        
        behavioral_data = []
        employees = Ishchi.objects.filter(is_active=True, rol='ISHCHI')
        
        for employee in employees:
            # Feedback alışverişi
            sent_feedback = QuickFeedback.objects.filter(
                from_user=employee,
                created_at__range=[start_date, end_date]
            ).count()
            
            received_feedback = QuickFeedback.objects.filter(
                to_user=employee,
                created_at__range=[start_date, end_date]
            ).count()
            
            # Login aktivliği
            days_since_login = 0
            if employee.last_login:
                days_since_login = (timezone.now().date() - employee.last_login.date()).days
            
            # Neqativ feedback nisbəti
            negative_feedback = QuickFeedback.objects.filter(
                to_user=employee,
                created_at__range=[start_date, end_date],
                rating__lt=3
            ).count()
            
            negative_ratio = negative_feedback / max(received_feedback, 1)
            
            behavioral_data.append({
                'employee_id': employee.id,
                'employee_name': employee.get_full_name(),
                'sent_feedback': sent_feedback,
                'received_feedback': received_feedback,
                'days_since_login': days_since_login,
                'negative_feedback_ratio': negative_ratio,
                'feedback_activity_score': sent_feedback + received_feedback
            })
        
        if len(behavioral_data) < self.min_data_points:
            return {"error": "Kifayətsiz davranış məlumatı"}
        
        df = pd.DataFrame(behavioral_data)
        
        # Davranış anomaliyalarını aşkarlayır
        behavioral_anomalies = {
            'login_anomalies': self._detect_login_anomalies(df),
            'feedback_anomalies': self._detect_feedback_anomalies(df),
            'isolation_behavioral': self._detect_behavioral_isolation_forest(df)
        }
        
        combined_behavioral = self._combine_behavioral_results(behavioral_anomalies, df)
        
        return {
            'period': f"Son {days_back} gün",
            'total_employees': len(behavioral_data),
            'behavioral_anomalies': len(combined_behavioral),
            'detection_methods': behavioral_anomalies,
            'combined_results': combined_behavioral,
            'analysis_date': timezone.now()
        }
    
    def detect_temporal_anomalies(self, employee: Ishchi, months_back: int = 6) -> Dict:
        """
        Müəyyən işçinin zaman ərzində performans dəyişikliklərini analiz edir
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        # Son dövrlərdə performans məlumatları
        cycles = QiymetlendirmeDovru.objects.filter(
            bashlama_tarixi__gte=start_date,
            bashlama_tarixi__lte=end_date
        ).order_by('bashlama_tarixi')
        
        temporal_data = []
        
        for cycle in cycles:
            evaluations = Qiymetlendirme.objects.filter(
                qiymetlendirilen=employee,
                dovr=cycle,
                status='COMPLETED'
            )
            
            if evaluations.exists():
                scores = []
                for evaluation in evaluations:
                    cavablar = evaluation.cavablar.all()
                    if cavablar:
                        avg_score = cavablar.aggregate(avg=Avg('xal'))['avg']
                        if avg_score:
                            scores.append(avg_score)
                
                if scores:
                    temporal_data.append({
                        'cycle': cycle.ad,
                        'cycle_start': cycle.bashlama_tarixi,
                        'avg_score': np.mean(scores),
                        'score_count': len(scores)
                    })
        
        if len(temporal_data) < 3:
            return {"error": "Zaman analizi üçün kifayətsiz məlumat"}
        
        df = pd.DataFrame(temporal_data)
        
        # Trend analizi
        trend_analysis = self._analyze_performance_trend(df)
        
        # Seasonality analizi
        seasonality = self._detect_seasonality(df)
        
        # Changepoint aşkarlaması
        changepoints = self._detect_changepoints(df)
        
        return {
            'employee': employee.get_full_name(),
            'analysis_period': f"Son {months_back} ay",
            'data_points': len(temporal_data),
            'trend_analysis': trend_analysis,
            'seasonality': seasonality,
            'changepoints': changepoints,
            'temporal_data': temporal_data
        }
    
    def _detect_statistical_outliers(self, df: pd.DataFrame) -> List[Dict]:
        """Z-score və IQR metodları ilə outlier aşkarlama"""
        outliers = []
        
        for column in ['avg_score', 'std_score', 'score_variance']:
            if column in df.columns:
                # IQR metodu
                Q1 = df[column].quantile(0.25)
                Q3 = df[column].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                column_outliers = df[
                    (df[column] < lower_bound) | (df[column] > upper_bound)
                ]
                
                for _, row in column_outliers.iterrows():
                    outliers.append({
                        'employee_id': row['employee_id'],
                        'employee_name': row['employee_name'],
                        'anomaly_type': f'{column}_outlier',
                        'value': row[column],
                        'method': 'IQR',
                        'bounds': {'lower': lower_bound, 'upper': upper_bound}
                    })
        
        return outliers
    
    def _detect_isolation_forest_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Isolation Forest algoritmi ilə anomaliy aşkarlama"""
        features = ['avg_score', 'std_score', 'evaluation_count', 'score_variance']
        available_features = [f for f in features if f in df.columns]
        
        if len(available_features) < 2:
            return []
        
        X = df[available_features].fillna(0)
        
        # Standardize edilmiş məlumatlar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Isolation Forest
        iso_forest = IsolationForest(
            contamination=self.contamination,
            random_state=42
        )
        
        anomaly_labels = iso_forest.fit_predict(X_scaled)
        anomaly_scores = iso_forest.decision_function(X_scaled)
        
        anomalies = []
        for i, (label, score) in enumerate(zip(anomaly_labels, anomaly_scores)):
            if label == -1:  # Anomaliy
                anomalies.append({
                    'employee_id': df.iloc[i]['employee_id'],
                    'employee_name': df.iloc[i]['employee_name'],
                    'anomaly_type': 'isolation_forest',
                    'anomaly_score': float(score),
                    'method': 'Isolation Forest',
                    'features_used': available_features
                })
        
        return anomalies
    
    def _detect_z_score_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Z-score əsaslı anomaliy aşkarlama"""
        anomalies = []
        
        for column in ['avg_score', 'std_score']:
            if column in df.columns:
                z_scores = np.abs(stats.zscore(df[column].fillna(df[column].mean())))
                
                for i, z_score in enumerate(z_scores):
                    if z_score > self.std_threshold:
                        anomalies.append({
                            'employee_id': df.iloc[i]['employee_id'],
                            'employee_name': df.iloc[i]['employee_name'],
                            'anomaly_type': f'{column}_zscore',
                            'z_score': float(z_score),
                            'value': df.iloc[i][column],
                            'method': 'Z-Score',
                            'threshold': self.std_threshold
                        })
        
        return anomalies
    
    def _detect_performance_clusters(self, df: pd.DataFrame) -> Dict:
        """DBSCAN klaster analizi"""
        features = ['avg_score', 'std_score', 'evaluation_count']
        available_features = [f for f in features if f in df.columns]
        
        if len(available_features) < 2:
            return {'clusters': 0, 'outliers': []}
        
        X = df[available_features].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # DBSCAN klaster analizi
        dbscan = DBSCAN(eps=0.5, min_samples=3)
        cluster_labels = dbscan.fit_predict(X_scaled)
        
        outliers = []
        for i, label in enumerate(cluster_labels):
            if label == -1:  # Noise point (outlier)
                outliers.append({
                    'employee_id': df.iloc[i]['employee_id'],
                    'employee_name': df.iloc[i]['employee_name'],
                    'anomaly_type': 'cluster_outlier',
                    'method': 'DBSCAN',
                    'cluster_label': int(label)
                })
        
        return {
            'clusters': len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0),
            'outliers': outliers,
            'noise_points': list(cluster_labels).count(-1)
        }
    
    def _detect_login_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Login davranışında anomaliyalar"""
        anomalies = []
        
        if 'days_since_login' in df.columns:
            mean_days = df['days_since_login'].mean()
            std_days = df['days_since_login'].std()
            
            for _, row in df.iterrows():
                days = row['days_since_login']
                if days > mean_days + 2 * std_days:  # 2 sigma qaydası
                    anomalies.append({
                        'employee_id': row['employee_id'],
                        'employee_name': row['employee_name'],
                        'anomaly_type': 'long_absence',
                        'days_since_login': days,
                        'method': 'Statistical Threshold',
                        'threshold': mean_days + 2 * std_days
                    })
        
        return anomalies
    
    def _detect_feedback_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Feedback davranışında anomaliyalar"""
        anomalies = []
        
        # Çox az feedback
        if 'feedback_activity_score' in df.columns:
            low_activity_threshold = df['feedback_activity_score'].quantile(0.1)
            
            low_activity = df[df['feedback_activity_score'] <= low_activity_threshold]
            for _, row in low_activity.iterrows():
                anomalies.append({
                    'employee_id': row['employee_id'],
                    'employee_name': row['employee_name'],
                    'anomaly_type': 'low_feedback_activity',
                    'activity_score': row['feedback_activity_score'],
                    'method': 'Percentile Analysis',
                    'threshold': low_activity_threshold
                })
        
        # Yüksək neqativ feedback
        if 'negative_feedback_ratio' in df.columns:
            high_negative_threshold = 0.6  # 60%-dən çox neqativ
            
            high_negative = df[df['negative_feedback_ratio'] > high_negative_threshold]
            for _, row in high_negative.iterrows():
                anomalies.append({
                    'employee_id': row['employee_id'],
                    'employee_name': row['employee_name'],
                    'anomaly_type': 'high_negative_feedback',
                    'negative_ratio': row['negative_feedback_ratio'],
                    'method': 'Threshold Analysis',
                    'threshold': high_negative_threshold
                })
        
        return anomalies
    
    def _detect_behavioral_isolation_forest(self, df: pd.DataFrame) -> List[Dict]:
        """Davranış məlumatları üçün Isolation Forest"""
        features = ['sent_feedback', 'received_feedback', 'days_since_login', 'negative_feedback_ratio']
        available_features = [f for f in features if f in df.columns]
        
        if len(available_features) < 2:
            return []
        
        X = df[available_features].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        iso_forest = IsolationForest(contamination=0.15, random_state=42)
        anomaly_labels = iso_forest.fit_predict(X_scaled)
        anomaly_scores = iso_forest.decision_function(X_scaled)
        
        anomalies = []
        for i, (label, score) in enumerate(zip(anomaly_labels, anomaly_scores)):
            if label == -1:
                anomalies.append({
                    'employee_id': df.iloc[i]['employee_id'],
                    'employee_name': df.iloc[i]['employee_name'],
                    'anomaly_type': 'behavioral_isolation',
                    'anomaly_score': float(score),
                    'method': 'Behavioral Isolation Forest'
                })
        
        return anomalies
    
    def _analyze_performance_trend(self, df: pd.DataFrame) -> Dict:
        """Performans trendini analiz edir"""
        if len(df) < 3:
            return {'trend': 'insufficient_data'}
        
        scores = df['avg_score'].values
        time_points = range(len(scores))
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(time_points, scores)
        
        trend_direction = 'stable'
        if slope > 0.1:
            trend_direction = 'improving'
        elif slope < -0.1:
            trend_direction = 'declining'
        
        return {
            'trend': trend_direction,
            'slope': float(slope),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'significance': 'significant' if p_value < 0.05 else 'not_significant'
        }
    
    def _detect_seasonality(self, df: pd.DataFrame) -> Dict:
        """Mövsümi dəyişiklikləri aşkarlayır"""
        if len(df) < 4:
            return {'seasonality': 'insufficient_data'}
        
        # Sadə mövsümi analiz - ortalama dəyişiklikləri
        scores = df['avg_score'].values
        mean_score = np.mean(scores)
        variations = [(score - mean_score) / mean_score for score in scores]
        
        max_variation = max(variations)
        min_variation = min(variations)
        
        seasonality_strength = max_variation - min_variation
        
        return {
            'seasonality_detected': seasonality_strength > 0.2,
            'seasonality_strength': float(seasonality_strength),
            'max_variation': float(max_variation),
            'min_variation': float(min_variation)
        }
    
    def _detect_changepoints(self, df: pd.DataFrame) -> List[Dict]:
        """Performansta kəskin dəyişiklik nöqtələrini aşkarlayır"""
        if len(df) < 4:
            return []
        
        scores = df['avg_score'].values
        changepoints = []
        
        # Sadə changepoint detection - ardıcıl fərqlər
        for i in range(1, len(scores) - 1):
            before_avg = np.mean(scores[:i+1])
            after_avg = np.mean(scores[i+1:])
            
            change_magnitude = abs(after_avg - before_avg)
            
            if change_magnitude > 1.0:  # 1 ballık dəyişiklik
                changepoints.append({
                    'position': i,
                    'cycle': df.iloc[i]['cycle'],
                    'before_avg': float(before_avg),
                    'after_avg': float(after_avg),
                    'change_magnitude': float(change_magnitude),
                    'change_direction': 'increase' if after_avg > before_avg else 'decrease'
                })
        
        return changepoints
    
    def _combine_anomaly_results(self, anomalies: Dict, df: pd.DataFrame) -> List[Dict]:
        """Müxtəlif metodların nəticələrini birləşdirir"""
        employee_anomalies = {}
        
        # Bütün anomaliyaları işçi ID-yə görə qruplaşdırır
        for method, method_anomalies in anomalies.items():
            if method == 'performance_clusters':
                method_anomalies = method_anomalies.get('outliers', [])
            
            for anomaly in method_anomalies:
                emp_id = anomaly['employee_id']
                if emp_id not in employee_anomalies:
                    employee_anomalies[emp_id] = {
                        'employee_id': emp_id,
                        'employee_name': anomaly['employee_name'],
                        'anomaly_methods': [],
                        'anomaly_count': 0,
                        'severity': 'LOW'
                    }
                
                employee_anomalies[emp_id]['anomaly_methods'].append({
                    'method': method,
                    'details': anomaly
                })
                employee_anomalies[emp_id]['anomaly_count'] += 1
        
        # Ciddiyyət səviyyəsini təyin edir
        for emp_data in employee_anomalies.values():
            count = emp_data['anomaly_count']
            if count >= 3:
                emp_data['severity'] = 'CRITICAL'
            elif count >= 2:
                emp_data['severity'] = 'HIGH'
            else:
                emp_data['severity'] = 'MEDIUM'
        
        return list(employee_anomalies.values())
    
    def _combine_behavioral_results(self, anomalies: Dict, df: pd.DataFrame) -> List[Dict]:
        """Davranış anomaliyalarını birləşdirir"""
        employee_anomalies = {}
        
        for method, method_anomalies in anomalies.items():
            for anomaly in method_anomalies:
                emp_id = anomaly['employee_id']
                if emp_id not in employee_anomalies:
                    employee_anomalies[emp_id] = {
                        'employee_id': emp_id,
                        'employee_name': anomaly['employee_name'],
                        'behavioral_anomalies': [],
                        'anomaly_count': 0,
                        'risk_level': 'LOW'
                    }
                
                employee_anomalies[emp_id]['behavioral_anomalies'].append({
                    'method': method,
                    'details': anomaly
                })
                employee_anomalies[emp_id]['anomaly_count'] += 1
        
        # Risk səviyyəsini təyin edir
        for emp_data in employee_anomalies.values():
            count = emp_data['anomaly_count']
            if count >= 3:
                emp_data['risk_level'] = 'CRITICAL'
            elif count >= 2:
                emp_data['risk_level'] = 'HIGH'
            else:
                emp_data['risk_level'] = 'MEDIUM'
        
        return list(employee_anomalies.values())
    
    def generate_anomaly_report(self, cycle: QiymetlendirmeDovru = None) -> Dict:
        """Tam anomaliy hesabatı yaradır"""
        performance_anomalies = self.detect_performance_anomalies(cycle)
        behavioral_anomalies = self.detect_behavioral_anomalies()
        
        # Risk Flag-ları yaradır
        if 'combined_results' in performance_anomalies:
            for anomaly in performance_anomalies['combined_results']:
                if anomaly['severity'] in ['HIGH', 'CRITICAL']:
                    try:
                        employee = Ishchi.objects.get(id=anomaly['employee_id'])
                        cycle_obj = cycle or QiymetlendirmeDovru.objects.filter(aktivdir=True).first()
                        
                        RiskFlag.objects.get_or_create(
                            employee=employee,
                            cycle=cycle_obj,
                            flag_type='STATISTICAL_ANOMALY',
                            defaults={
                                'severity': RiskFlag.Severity.HIGH if anomaly['severity'] == 'HIGH' else RiskFlag.Severity.CRITICAL,
                                'risk_score': anomaly['anomaly_count'] * 2,
                                'details': {
                                    'anomaly_methods': anomaly['anomaly_methods'],
                                    'detection_type': 'statistical_performance'
                                },
                                'ai_confidence': 0.9
                            }
                        )
                    except Exception as e:
                        logger.error(f"Risk Flag yaradılması xətası: {e}")
        
        return {
            'performance_anomalies': performance_anomalies,
            'behavioral_anomalies': behavioral_anomalies,
            'summary': {
                'total_performance_anomalies': len(performance_anomalies.get('combined_results', [])),
                'total_behavioral_anomalies': len(behavioral_anomalies.get('combined_results', [])),
                'critical_employees': [
                    a for a in performance_anomalies.get('combined_results', [])
                    if a.get('severity') == 'CRITICAL'
                ] + [
                    a for a in behavioral_anomalies.get('combined_results', [])
                    if a.get('risk_level') == 'CRITICAL'
                ]
            },
            'generated_at': timezone.now()
        }