# -*- coding: utf-8 -*-

from transformers import AutoConfig, AutoModel, AutoModelForCausalLM

from rwkvfla.models.hgrn2.configuration_hgrn2 import HGRN2Config
from rwkvfla.models.hgrn2.modeling_hgrn2 import HGRN2ForCausalLM, HGRN2Model

AutoConfig.register(HGRN2Config.model_type, HGRN2Config)
AutoModel.register(HGRN2Config, HGRN2Model)
AutoModelForCausalLM.register(HGRN2Config, HGRN2ForCausalLM)


__all__ = ['HGRN2Config', 'HGRN2ForCausalLM', 'HGRN2Model']
