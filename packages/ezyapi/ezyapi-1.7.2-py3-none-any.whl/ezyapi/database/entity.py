"""
엔티티 기본 클래스 모듈

이 모듈은 모든 데이터 엔티티의 기본이 되는 클래스를 제공합니다.
"""

from typing import List, TypeVar, Any

T = TypeVar('T')

def OneToMany(target_entity, mapped_by: str = None):
    return {
        '_relation_type': 'one_to_many',
        '_target_entity': target_entity,
        '_mapped_by': mapped_by
    }

def ManyToOne(target_entity, foreign_key: str = None):
    return {
        '_relation_type': 'many_to_one', 
        '_target_entity': target_entity,
        '_foreign_key': foreign_key
    }

class EzyEntityBase:
    """
    모든 데이터 엔티티의 기본 클래스입니다.
    
    이 클래스를 상속받아 새로운 엔티티 타입을 정의할 수 있습니다.
    모든 엔티티는 기본적으로 id 속성을 가집니다.
    
    Attributes:
        id (int, optional): 엔티티의 고유 식별자. 기본값은 None입니다.
    """
    id: int = None
    
    def get_primary_key_info(self):
        """
        Primary key 정보를 반환합니다.
        
        Returns:
            dict: primary key 필드명과 메타데이터 정보
        """
        from ezyapi.database.decorators import get_column_metadata
        
        metadata = get_column_metadata(self.__class__)
        
        for field_name, meta in metadata.items():
            if meta.primary:
                return {
                    'field_name': field_name,
                    'auto_increment': meta.auto_increment,
                    'column_type': meta.column_type
                }
        
        return {
            'field_name': 'id',
            'auto_increment': True,
            'column_type': None
        }