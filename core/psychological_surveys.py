# core/psychological_surveys.py

from django.utils import timezone
from typing import Dict, List
import json

from .models import PsychologicalRiskSurvey, PsychologicalRiskResponse, Ishchi


class PsychologicalSurveyManager:
    """
    Psixoloji risk sorğularını idarə edən sinif.
    Standart sorğuları yaradır və cavabları analiz edir.
    """
    
    def __init__(self):
        self.default_surveys = {
            'WHO5_WELLBEING': self._create_who5_survey,
            'BURNOUT_ASSESSMENT': self._create_burnout_survey,
            'STRESS_LEVEL': self._create_stress_survey,
            'JOB_SATISFACTION': self._create_job_satisfaction_survey,
            'WORK_LIFE_BALANCE': self._create_work_life_balance_survey
        }
    
    def create_default_surveys(self, created_by: Ishchi) -> List[PsychologicalRiskSurvey]:
        """Standart psixoloji sorğuları yaradır"""
        surveys = []
        
        for survey_type, creator_func in self.default_surveys.items():
            # Artıq mövcud olmadığını yoxla
            existing = PsychologicalRiskSurvey.objects.filter(
                survey_type=survey_type,
                is_active=True
            ).first()
            
            if not existing:
                survey_data = creator_func()
                survey = PsychologicalRiskSurvey.objects.create(
                    title=survey_data['title'],
                    survey_type=survey_type,
                    questions=survey_data['questions'],
                    scoring_method=survey_data['scoring_method'],
                    risk_thresholds=survey_data['risk_thresholds'],
                    is_active=True,
                    is_anonymous=survey_data.get('is_anonymous', True),
                    created_by=created_by
                )
                surveys.append(survey)
        
        return surveys
    
    def _create_who5_survey(self) -> Dict:
        """WHO-5 Wellbeing Index sorğusu"""
        return {
            'title': 'WHO-5 Rifah İndeksi',
            'questions': [
                {
                    'id': 1,
                    'text': 'Son iki həftə ərzində özümü şən və yaxşı əhval-ruhiyyədə hiss etmişəm',
                    'type': 'likert_6',
                    'options': [
                        {'value': 0, 'label': 'Heç vaxt'},
                        {'value': 1, 'label': 'Nadir hallarda'},
                        {'value': 2, 'label': 'Vaxtaşırı'},
                        {'value': 3, 'label': 'Yarısından çox'},
                        {'value': 4, 'label': 'Çox vaxt'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 2,
                    'text': 'Son iki həftə ərzində özümü sakit və rahat hiss etmişəm',
                    'type': 'likert_6',
                    'options': [
                        {'value': 0, 'label': 'Heç vaxt'},
                        {'value': 1, 'label': 'Nadir hallarda'},
                        {'value': 2, 'label': 'Vaxtaşırı'},
                        {'value': 3, 'label': 'Yarısından çox'},
                        {'value': 4, 'label': 'Çox vaxt'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 3,
                    'text': 'Son iki həftə ərzində özümü aktiv və enerjili hiss etmişəm',
                    'type': 'likert_6',
                    'options': [
                        {'value': 0, 'label': 'Heç vaxt'},
                        {'value': 1, 'label': 'Nadir hallarda'},
                        {'value': 2, 'label': 'Vaxtaşırı'},
                        {'value': 3, 'label': 'Yarısından çox'},
                        {'value': 4, 'label': 'Çox vaxt'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 4,
                    'text': 'Son iki həftə ərzində yuxudan oyandığımda özümü dincəlmiş və dinc hiss etmişəm',
                    'type': 'likert_6',
                    'options': [
                        {'value': 0, 'label': 'Heç vaxt'},
                        {'value': 1, 'label': 'Nadir hallarda'},
                        {'value': 2, 'label': 'Vaxtaşırı'},
                        {'value': 3, 'label': 'Yarısından çox'},
                        {'value': 4, 'label': 'Çox vaxt'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 5,
                    'text': 'Son iki həftə ərzində gündəlik həyatım maraqlı şeylərlə dolu olmuşdur',
                    'type': 'likert_6',
                    'options': [
                        {'value': 0, 'label': 'Heç vaxt'},
                        {'value': 1, 'label': 'Nadir hallarda'},
                        {'value': 2, 'label': 'Vaxtaşırı'},
                        {'value': 3, 'label': 'Yarısından çox'},
                        {'value': 4, 'label': 'Çox vaxt'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                }
            ],
            'scoring_method': {
                'type': 'sum',
                'description': 'Bütün cavabların cəmi (0-25 bal)',
                'interpretation': {
                    '0-5': 'Çox zəif rifah',
                    '6-10': 'Zəif rifah',
                    '11-15': 'Orta rifah',
                    '16-20': 'Yaxşı rifah',
                    '21-25': 'Əla rifah'
                }
            },
            'risk_thresholds': {
                'very_high': 21,  # Çox yüksək rifah
                'high': 16,       # Yüksək rifah
                'moderate': 11,   # Orta rifah
                'low': 6,         # Aşağı rifah
                'very_low': 0     # Çox aşağı rifah
            },
            'is_anonymous': True
        }
    
    def _create_burnout_survey(self) -> Dict:
        """Tükənmişlik qiymətləndirmə sorğusu"""
        return {
            'title': 'Tükənmişlik Qiymətləndirməsi',
            'questions': [
                {
                    'id': 1,
                    'text': 'İşimdən emosional olaraq tükənmiş hiss edirəm',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Heç vaxt'},
                        {'value': 2, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 4, 'label': 'Tez-tez'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 2,
                    'text': 'İş günü sonunda özümü tamamilə tükənmiş hiss edirəm',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Heç vaxt'},
                        {'value': 2, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 4, 'label': 'Tez-tez'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 3,
                    'text': 'İşlə bağlı insanlarla işləmək məni çox yorur',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Heç vaxt'},
                        {'value': 2, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 4, 'label': 'Tez-tez'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 4,
                    'text': 'Səhər işə getməyi düşünəndə özümü yorğun hiss edirəm',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Heç vaxt'},
                        {'value': 2, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 4, 'label': 'Tez-tez'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 5,
                    'text': 'İşimin məndən çox şey tələb etdiyini hiss edirəm',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Heç vaxt'},
                        {'value': 2, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 4, 'label': 'Tez-tez'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 6,
                    'text': 'İşdə problemləri effektiv şəkildə həll edə bilirəm',
                    'type': 'likert_5',
                    'reverse_scored': True,
                    'options': [
                        {'value': 5, 'label': 'Heç vaxt'},
                        {'value': 4, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 2, 'label': 'Tez-tez'},
                        {'value': 1, 'label': 'Həmişə'}
                    ]
                }
            ],
            'scoring_method': {
                'type': 'average',
                'description': 'Cavabların ortalama dəyəri (1-5 bal)',
                'interpretation': {
                    '1.0-2.0': 'Aşağı tükənmişlik',
                    '2.1-3.0': 'Orta tükənmişlik',
                    '3.1-4.0': 'Yüksək tükənmişlik',
                    '4.1-5.0': 'Çox yüksək tükənmişlik'
                }
            },
            'risk_thresholds': {
                'very_high': 4.1,
                'high': 3.1,
                'moderate': 2.1,
                'low': 1.0,
                'very_low': 0
            },
            'is_anonymous': True
        }
    
    def _create_stress_survey(self) -> Dict:
        """Stress səviyyəsi sorğusu"""
        return {
            'title': 'İş Stress Səviyyəsi',
            'questions': [
                {
                    'id': 1,
                    'text': 'İşimdə hiss etdiyim stress səviyyəsi',
                    'type': 'scale_1_10',
                    'description': '1 = Heç stress yoxdur, 10 = Çox yüksək stress'
                },
                {
                    'id': 2,
                    'text': 'İş yükümün idarə edilə bilən olması',
                    'type': 'likert_5',
                    'reverse_scored': True,
                    'options': [
                        {'value': 5, 'label': 'Tamamilə razıyam'},
                        {'value': 4, 'label': 'Razıyam'},
                        {'value': 3, 'label': 'Neytralam'},
                        {'value': 2, 'label': 'Razı deyiləm'},
                        {'value': 1, 'label': 'Tamamilə razı deyiləm'}
                    ]
                },
                {
                    'id': 3,
                    'text': 'İş müddətində həyəcan və ya narahatlıq hiss edirəm',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Heç vaxt'},
                        {'value': 2, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 4, 'label': 'Tez-tez'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 4,
                    'text': 'İş stresinin şəxsi həyatıma təsiri',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Heç təsir etmir'},
                        {'value': 2, 'label': 'Az təsir edir'},
                        {'value': 3, 'label': 'Orta dərəcədə təsir edir'},
                        {'value': 4, 'label': 'Çox təsir edir'},
                        {'value': 5, 'label': 'Çox güclü təsir edir'}
                    ]
                }
            ],
            'scoring_method': {
                'type': 'weighted_average',
                'weights': [0.4, 0.2, 0.2, 0.2],
                'description': 'Çəkili ortalama (1-10 bal)',
                'interpretation': {
                    '1-3': 'Aşağı stress',
                    '4-6': 'Orta stress',
                    '7-8': 'Yüksək stress',
                    '9-10': 'Çox yüksək stress'
                }
            },
            'risk_thresholds': {
                'very_high': 9,
                'high': 7,
                'moderate': 4,
                'low': 1,
                'very_low': 0
            },
            'is_anonymous': True
        }
    
    def _create_job_satisfaction_survey(self) -> Dict:
        """İş məmnunluğu sorğusu"""
        return {
            'title': 'İş Məmnunluğu Sorğusu',
            'questions': [
                {
                    'id': 1,
                    'text': 'Ümumi olaraq işimdən məmnunam',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Tamamilə razı deyiləm'},
                        {'value': 2, 'label': 'Razı deyiləm'},
                        {'value': 3, 'label': 'Neytralam'},
                        {'value': 4, 'label': 'Razıyam'},
                        {'value': 5, 'label': 'Tamamilə razıyam'}
                    ]
                },
                {
                    'id': 2,
                    'text': 'İşim maraqlı və meydan oxuyandır',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Tamamilə razı deyiləm'},
                        {'value': 2, 'label': 'Razı deyiləm'},
                        {'value': 3, 'label': 'Neytralam'},
                        {'value': 4, 'label': 'Razıyam'},
                        {'value': 5, 'label': 'Tamamilə razıyam'}
                    ]
                },
                {
                    'id': 3,
                    'text': 'İş mühitim əlverişlidir',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Tamamilə razı deyiləm'},
                        {'value': 2, 'label': 'Razı deyiləm'},
                        {'value': 3, 'label': 'Neytralam'},
                        {'value': 4, 'label': 'Razıyam'},
                        {'value': 5, 'label': 'Tamamilə razıyam'}
                    ]
                },
                {
                    'id': 4,
                    'text': 'Rəhbərimdən aldığım dəstəkdən məmnunam',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Tamamilə razı deyiləm'},
                        {'value': 2, 'label': 'Razı deyiləm'},
                        {'value': 3, 'label': 'Neytralam'},
                        {'value': 4, 'label': 'Razıyam'},
                        {'value': 5, 'label': 'Tamamilə razıyam'}
                    ]
                },
                {
                    'id': 5,
                    'text': 'İşyerindəki həmkarlarımla münasibətlərimdən məmnunam',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Tamamilə razı deyiləm'},
                        {'value': 2, 'label': 'Razı deyiləm'},
                        {'value': 3, 'label': 'Neytralam'},
                        {'value': 4, 'label': 'Razıyam'},
                        {'value': 5, 'label': 'Tamamilə razıyam'}
                    ]
                }
            ],
            'scoring_method': {
                'type': 'average',
                'description': 'Cavabların ortalama dəyəri (1-5 bal)',
                'interpretation': {
                    '1.0-2.0': 'Çox aşağı məmnunluq',
                    '2.1-3.0': 'Aşağı məmnunluq',
                    '3.1-4.0': 'Orta məmnunluq',
                    '4.1-5.0': 'Yüksək məmnunluq'
                }
            },
            'risk_thresholds': {
                'very_high': 4.1,  # Yüksək məmnunluq = aşağı risk
                'high': 3.1,
                'moderate': 2.1,
                'low': 1.0,
                'very_low': 0
            },
            'is_anonymous': True
        }
    
    def _create_work_life_balance_survey(self) -> Dict:
        """İş-həyat balansı sorğusu"""
        return {
            'title': 'İş-Həyat Balansı',
            'questions': [
                {
                    'id': 1,
                    'text': 'İş və şəxsi həyat arasında balansı qorumaq mənə çətin gəlir',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Heç vaxt'},
                        {'value': 2, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 4, 'label': 'Tez-tez'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 2,
                    'text': 'İş saatlarım şəxsi həyatımla müdaxilə edir',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Heç vaxt'},
                        {'value': 2, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 4, 'label': 'Tez-tez'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 3,
                    'text': 'Ailə və dostlarımla keyfiyyətli vaxt keçirə bilirəm',
                    'type': 'likert_5',
                    'reverse_scored': True,
                    'options': [
                        {'value': 5, 'label': 'Heç vaxt'},
                        {'value': 4, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 2, 'label': 'Tez-tez'},
                        {'value': 1, 'label': 'Həmişə'}
                    ]
                },
                {
                    'id': 4,
                    'text': 'İş stresi evdə də davam edir',
                    'type': 'likert_5',
                    'options': [
                        {'value': 1, 'label': 'Heç vaxt'},
                        {'value': 2, 'label': 'Nadir hallarda'},
                        {'value': 3, 'label': 'Bəzən'},
                        {'value': 4, 'label': 'Tez-tez'},
                        {'value': 5, 'label': 'Həmişə'}
                    ]
                }
            ],
            'scoring_method': {
                'type': 'average',
                'description': 'Cavabların ortalama dəyəri (1-5 bal)',
                'interpretation': {
                    '1.0-2.0': 'Yaxşı balans',
                    '2.1-3.0': 'Orta balans',
                    '3.1-4.0': 'Zəif balans',
                    '4.1-5.0': 'Çox zəif balans'
                }
            },
            'risk_thresholds': {
                'very_high': 4.1,
                'high': 3.1,
                'moderate': 2.1,
                'low': 1.0,
                'very_low': 0
            },
            'is_anonymous': True
        }
    
    def calculate_survey_score(self, survey: PsychologicalRiskSurvey, answers: Dict) -> float:
        """Sorğu cavablarını əsasən xal hesablayır"""
        scoring_method = survey.scoring_method
        questions = survey.questions
        
        total_score = 0
        valid_answers = 0
        
        if scoring_method['type'] == 'sum':
            for question in questions:
                question_id = str(question['id'])
                if question_id in answers:
                    total_score += float(answers[question_id])
                    valid_answers += 1
        
        elif scoring_method['type'] == 'average':
            scores = []
            for question in questions:
                question_id = str(question['id'])
                if question_id in answers:
                    score = float(answers[question_id])
                    # Reverse scoring yoxla
                    if question.get('reverse_scored', False):
                        max_value = max(opt['value'] for opt in question['options'])
                        min_value = min(opt['value'] for opt in question['options'])
                        score = max_value + min_value - score
                    scores.append(score)
            
            if scores:
                total_score = sum(scores) / len(scores)
                valid_answers = len(scores)
        
        elif scoring_method['type'] == 'weighted_average':
            weights = scoring_method.get('weights', [])
            weighted_scores = []
            
            for i, question in enumerate(questions):
                question_id = str(question['id'])
                if question_id in answers and i < len(weights):
                    score = float(answers[question_id])
                    if question.get('reverse_scored', False):
                        max_value = max(opt['value'] for opt in question['options'])
                        min_value = min(opt['value'] for opt in question['options'])
                        score = max_value + min_value - score
                    
                    # Stress survey üçün xüsusi normallaşdırma
                    if question.get('type') == 'scale_1_10':
                        # 1-10 skalasını 1-5 skalasına çevir
                        score = (score - 1) * 4 / 9 + 1
                    
                    weighted_scores.append(score * weights[i])
            
            if weighted_scores:
                total_score = sum(weighted_scores) / sum(weights[:len(weighted_scores)])
                valid_answers = len(weighted_scores)
        
        return total_score if valid_answers > 0 else 0.0
    
    def analyze_survey_response(self, response: PsychologicalRiskResponse) -> Dict:
        """Sorğu cavabını analiz edir və tövsiyələr verir"""
        survey = response.survey
        score = response.total_score
        risk_level = response.risk_level
        
        analysis = {
            'score': score,
            'risk_level': risk_level,
            'interpretation': self._get_score_interpretation(survey, score),
            'recommendations': self._get_recommendations(survey.survey_type, risk_level),
            'requires_attention': response.requires_attention
        }
        
        return analysis
    
    def _get_score_interpretation(self, survey: PsychologicalRiskSurvey, score: float) -> str:
        """Xala əsasən interpretasiya qaytarır"""
        interpretation = survey.scoring_method.get('interpretation', {})
        
        for range_str, meaning in interpretation.items():
            if '-' in range_str:
                min_val, max_val = map(float, range_str.split('-'))
                if min_val <= score <= max_val:
                    return meaning
            else:
                # Tək dəyər
                if float(range_str) == score:
                    return meaning
        
        return "Naməlum nəticə"
    
    def _get_recommendations(self, survey_type: str, risk_level: str) -> List[str]:
        """Risk səviyyəsinə əsasən tövsiyələr qaytarır"""
        recommendations_map = {
            'WHO5_WELLBEING': {
                'VERY_HIGH': [
                    'Möhtəşəm! Əla rifah səviyyənizi qoruyun',
                    'Digər həmkarlarınızla təcrübənizi bölüşün'
                ],
                'HIGH': [
                    'Yaxşı rifah səviyyəniz var',
                    'Mövcud müsbət vərdişləri davam etdirin'
                ],
                'MODERATE': [
                    'Rifah səviyyənizi artırmaq üçün özünüzə daha çox vaxt ayırın',
                    'Fiziki aktivlik və sosial əlaqələri artırın'
                ],
                'LOW': [
                    'Professional dəstək almağı düşünün',
                    'Stress idarəetmə üsullarını öyrənin',
                    'Rəhbərinizlə iş yükünüz barədə danışın'
                ],
                'VERY_LOW': [
                    'Mütləq professional psixoloji dəstək alın',
                    'HR departamenti ilə əlaqə saxlayın',
                    'Təcili olaraq iş yükünüzü azaltmağı düşünün'
                ]
            },
            'BURNOUT_ASSESSMENT': {
                'VERY_HIGH': [
                    'Təcili tədbirlər tələb olunur - professional kömək alın',
                    'İş yükünüzü azaltmaq üçün rəhbərinizlə danışın',
                    'Məzuniyyət götürməyi düşünün'
                ],
                'HIGH': [
                    'Tükənmişlik əlamətləri var - diqqət tələb olunur',
                    'Stress idarəetmə texnikalarını tətbiq edin',
                    'Fiziki aktivlik və dincəlmə vaxtını artırın'
                ],
                'MODERATE': [
                    'Özünüzə qulluq etməyə diqqət yetirin',
                    'İş-həyat balansını qoruyun',
                    'Müntəzəm fasilələr götürün'
                ],
                'LOW': [
                    'Yaxşı vəziyyətdəsiniz',
                    'Mövcud sağlam vərdişləri davam etdirin'
                ]
            },
            'STRESS_LEVEL': {
                'VERY_HIGH': [
                    'Təcili stress idarəetmə tələb olunur',
                    'Professional psixoloji dəstək alın',
                    'İş yükünüzü bölüşdürmək üçün komanda ilə işləyin'
                ],
                'HIGH': [
                    'Stress səviyyənizi azaltmağa diqqət yetirin',
                    'Nəfəs texnikaları və meditasiya sınayın',
                    'Prioritetlərinizi yenidən qiymətləndirin'
                ],
                'MODERATE': [
                    'Stress idarəetmə bacarıqlarınızı inkişaf etdirin',
                    'Müntəzəm idman və dincəlmə'
                ],
                'LOW': [
                    'Yaxşı stress idarəetmə səviyyəniz var',
                    'Bu vəziyyəti qoruyun'
                ]
            },
            'JOB_SATISFACTION': {
                'HIGH': [
                    'İşinizdən yüksək məmnunluq - əla!',
                    'Bu müsbət təcrübəni digərlərlə bölüşün'
                ],
                'MODERATE': [
                    'İş məmnunluğunuzu artırmaq üçün yeni çağırışlar axtarın',
                    'Professional inkişaf imkanlarını araşdırın'
                ],
                'LOW': [
                    'İş məmnunluğunuzu artırmaq üçün konkret addımlar atın',
                    'Rəhbərinizlə karyera inkişafı barədə danışın'
                ],
                'VERY_LOW': [
                    'Ciddi iş məmnunluğu problemi var',
                    'HR departamenti ilə görüşün',
                    'Karyera dəyişikliyi seçimlərini araşdırın'
                ]
            },
            'WORK_LIFE_BALANCE': {
                'VERY_HIGH': [
                    'İş-həyat balansı ciddi problemi var',
                    'İş saatlarınızı yenidən planlaşdırın',
                    'Şəxsi həyat üçün sərhədlər qoyun'
                ],
                'HIGH': [
                    'Balans problemləri mövcuddur',
                    'Vaxt idarəetmə bacarıqlarını təkmilləşdirin',
                    'Ailə və dostlar üçün daha çox vaxt ayırın'
                ],
                'MODERATE': [
                    'Orta səviyyədə balans - təkmilləşdirmə mümkündür',
                    'Hobbi və şəxsi maraqlar üçün vaxt yaradın'
                ],
                'LOW': [
                    'Yaxşı iş-həyat balansınız var',
                    'Bu müsbət vəziyyəti qoruyun'
                ]
            }
        }
        
        return recommendations_map.get(survey_type, {}).get(risk_level, ['Ümumi məsləhət: Professional dəstək almağı düşünün'])
    
    def get_survey_analytics(self, survey: PsychologicalRiskSurvey) -> Dict:
        """Sorğu üçün analitik məlumatlar"""
        responses = survey.responses.all()
        
        if not responses.exists():
            return {'error': 'Cavab tapılmadı'}
        
        total_responses = responses.count()
        if total_responses == 0:
            return {'error': 'Cavab tapılmadı'}
        
        # Risk səviyyəsi paylanması
        risk_distribution = {}
        for choice in PsychologicalRiskSurvey.RiskLevel.choices:
            risk_level = choice[0]
            count = responses.filter(risk_level=risk_level).count()
            risk_distribution[risk_level] = {
                'count': count,
                'percentage': round((count / total_responses) * 100, 1) if total_responses else 0
            }
        
        # Ortalama xal
        avg_score = sum(r.total_score for r in responses) / total_responses if total_responses else 0
        
        # Diqqət tələb edən cavablar
        attention_required = responses.filter(requires_attention=True).count()
        
        return {
            'survey_title': survey.title,
            'total_responses': total_responses,
            'average_score': round(avg_score, 2),
            'risk_distribution': risk_distribution,
            'attention_required': attention_required,
            'completion_rate': round((total_responses / Ishchi.objects.filter(is_active=True, rol='ISHCHI').count()) * 100, 1) if Ishchi.objects.filter(is_active=True, rol='ISHCHI').count() else 0
        }