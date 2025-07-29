import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, config_path: str = '.cursor-init.yaml'):
        self.config_path = config_path
        self._config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file) or {}
                return self._merge_with_defaults(config_data)
        except yaml.YAMLError as e:
            print(f'Warning: Invalid YAML in {self.config_path}: {e}')
            print('Falling back to default configuration.')
            return self._get_default_config()
        except Exception as e:
            print(f'Warning: Could not read {self.config_path}: {e}')
            print('Falling back to default configuration.')
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'templates': {
                'adr': 'nygard_style',
                'architecture': 'google_style',
                'onboarding': 'general'
            },
            'custom_template_paths': []
        }
    
    def _merge_with_defaults(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        default_config = self._get_default_config()
        
        if 'templates' not in config_data:
            config_data['templates'] = {}
        
        for key, default_value in default_config['templates'].items():
            if key not in config_data['templates']:
                config_data['templates'][key] = default_value
        
        if 'custom_template_paths' not in config_data:
            config_data['custom_template_paths'] = []
        
        return config_data
    
    def get_template_variant(self, doc_type: str) -> str:
        return self._config_data.get('templates', {}).get(doc_type, 'default')
    
    def get_custom_template_paths(self) -> List[Dict[str, str]]:
        return self._config_data.get('custom_template_paths', [])
    
    def get_template_path(self, doc_type: str) -> Optional[str]:
        variant = self.get_template_variant(doc_type)
        
        template_mappings = {
            'adr': {
                'nygard_style': '.cursor/templates/adr/adr_template_nygard.md',
                'full': '.cursor/templates/adr/adr_template_full.md',
                'lightweight': '.cursor/templates/adr/adr_template_lightweight.md'
            },
            'architecture': {
                'google_style': '.cursor/templates/architecture/architecture_google.md',
                'enterprise': '.cursor/templates/architecture/architecture_enterprise.md',
                'arc42': '.cursor/templates/architecture/architecture_arc.md'
            },
            'onboarding': {
                'general': '.cursor/templates/onboarding/onboarding_general.md',
                'python': '.cursor/templates/onboarding/onboarding_python.md',
                'frontend': '.cursor/templates/onboarding/onboarding_frontend.md'
            }
        }
        
        if doc_type in template_mappings and variant in template_mappings[doc_type]:
            return template_mappings[doc_type][variant]
        
        return None
    
    def add_custom_template(self, name: str, path: str) -> bool:
        if not os.path.exists(path):
            return False
        
        custom_templates = self.get_custom_template_paths()
        
        for template in custom_templates:
            if template.get('path') == path:
                return False
        
        custom_templates.append({'name': name, 'path': path})
        self._config_data['custom_template_paths'] = custom_templates
        
        return self._save_config()
    
    def _save_config(self) -> bool:
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self._config_data, file, default_flow_style=False, sort_keys=False)
            return True
        except Exception as e:
            print(f'Error saving configuration to {self.config_path}: {e}')
            return False


def load_config(config_path: str = '.cursor-init.yaml') -> Config:
    return Config(config_path) 