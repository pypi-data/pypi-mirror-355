import logging
import vllm

import graphsignal
from graphsignal.recorders.base_recorder import BaseRecorder
from graphsignal.recorders.instrumentation import trace_method, profile_method, patch_method, parse_semver, compare_semver
from graphsignal.profiles import EventAverages

logger = logging.getLogger('graphsignal')

class VLLMRecorder(BaseRecorder):
    def __init__(self):
        self._active_profile = None
        self._profiling = False

    def setup(self):
        if not graphsignal._tracer.auto_instrument:
            return

        version = vllm.__version__
        self._library_version = version
        parsed_version = parse_semver(version)

        if compare_semver(parsed_version, (0, 8, 0)) >= 0:
            def read_kwarg(store, kwargs, name, default=None):
                if name in kwargs:
                    store[name] = str(kwargs[name])
                elif default is not None:
                    store[name] = str(default)

            def after_llm_init(args, kwargs, ret, exc, context):
                llm_obj = args[0]
                llm_tags = {}
                llm_params = {}

                model = None
                if len(args) > 1 and args[1] is not None:
                    model = args[1]
                read_kwarg(llm_tags, kwargs, 'model', default=model)
                read_kwarg(llm_params, kwargs, 'model', default=model)
                read_kwarg(llm_params, kwargs, 'tokenizer')
                read_kwarg(llm_params, kwargs, 'tensor_parallel_size')
                read_kwarg(llm_params, kwargs, 'dtype')
                read_kwarg(llm_params, kwargs, 'quantization')
                read_kwarg(llm_params, kwargs, 'gpu_memory_utilization')
                read_kwarg(llm_params, kwargs, 'swap_space')
                read_kwarg(llm_params, kwargs, 'cpu_offload_gb')
                read_kwarg(llm_params, kwargs, 'enforce_eager')
                read_kwarg(llm_params, kwargs, 'max_seq_len_to_capture')
                read_kwarg(llm_params, kwargs, 'disable_custom_all_reduce')
                read_kwarg(llm_params, kwargs, 'disable_async_output_proc')

                def trace_generate(span, args, kwargs, ret, exc):
                    for param_name, param_value in llm_tags.items():
                        span.set_tag(param_name, param_value)
                    for param_name, param_value in llm_params.items():
                        span.set_param(param_name, param_value)
                    #sampling_params = kwargs.get('sampling_params', None)

                trace_method(llm_obj, 'generate', 'LLM.generate', trace_func=trace_generate)

            patch_method(vllm.LLM, '__init__', after_func=after_llm_init)

            '''def after_llm_engine_init(args, kwargs, ret, exc, context):
                llm_engine = args[0]
                trace_method(llm_engine, 'generate', 'LLMEngine.generate', trace_func=trace_generate)

            patch_method(vllm.llm_engine.LLMEngine, '__init__', after_func=after_llm_engine_init)'''

            '''def after_async_llm_init(args, kwargs, ret, exc, context):
                llm_engine = args[0]

                trace_method(llm_engine, 'generate', 'AsyncLLMEngine.generate', trace_func=trace_generate)

            patch_method(vllm.engine.async_llm_engine.AsyncLLMEngine, '__init__', after_func=after_async_llm_init)'''
        else:
            logger.debug('VLLM tracing is only supported for >= 0.8.0.')
            return

    def shutdown(self):
        pass
