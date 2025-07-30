# -*- coding: utf-8 -*-

from transformers import AutoConfig, AutoModel, AutoModelForCausalLM

from rwkvfla.models.samba.configuration_samba import SambaConfig
from rwkvfla.models.samba.modeling_samba import SambaBlock, SambaForCausalLM, SambaModel

AutoConfig.register(SambaConfig.model_type, SambaConfig, True)
AutoModel.register(SambaConfig, SambaModel, True)
AutoModelForCausalLM.register(SambaConfig, SambaForCausalLM, True)


__all__ = ['SambaConfig', 'SambaForCausalLM', 'SambaModel', 'SambaBlock']
