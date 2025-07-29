"""
LangChain adapter for AgentDebugger SDK.

Provides specialized debugging support for LangChain agents, chains,
and related components with native LangChain integration.
"""

import re
from typing import Any, Dict, List, Optional, Union
from .base import BaseAdapter, FrameworkType, FrameworkInfo, NormalizedTrace


class LangChainAdapter(BaseAdapter):
    """
    Specialized adapter for LangChain framework integration.
    
    Provides native debugging support for LangChain chains, agents,
    memory systems, and LLM interactions.
    """
    
    def __init__(self, debug_config: Dict[str, Any]):
        """
        Initialize LangChain adapter.
        
        Args:
            debug_config: Configuration dictionary for debugging
        """
        super().__init__(debug_config)
        self.detected_components = {
            "chains": [],
            "agents": [],
            "llms": [],
            "memory": [],
            "tools": []
        }
    
    def detect_framework(self, agent_instance: Any) -> FrameworkInfo:
        """
        Detect if agent instance is using LangChain framework.
        
        Args:
            agent_instance: Agent instance to analyze
            
        Returns:
            FrameworkInfo with LangChain detection results
        """
        confidence = 0.0
        detected_modules = []
        agent_class = agent_instance.__class__.__name__
        module_name = agent_instance.__class__.__module__
        
        # Check module path for LangChain indicators
        if "langchain" in module_name.lower():
            confidence += 0.8
            detected_modules.append(module_name)
        
        # Check class name for LangChain patterns
        langchain_class_patterns = [
            r".*Chain$", r".*Agent$", r".*LLM$", r".*Memory$",
            r".*Tool$", r".*Retriever$", r".*Loader$"
        ]
        
        for pattern in langchain_class_patterns:
            if re.match(pattern, agent_class):
                confidence += 0.3
                break
        
        # Check for LangChain-specific attributes
        langchain_attributes = [
            "run", "arun", "invoke", "ainvoke", "predict", "call",
            "memory", "tools", "llm", "chain", "prompt", "callbacks"
        ]
        
        found_attributes = []
        for attr in langchain_attributes:
            if hasattr(agent_instance, attr):
                found_attributes.append(attr)
                confidence += 0.1
        
        # Check for LangChain imports in the system
        try:
            import sys
            langchain_modules = [mod for mod in sys.modules.keys() if "langchain" in mod]
            if langchain_modules:
                confidence += 0.2
                detected_modules.extend(langchain_modules[:5])  # Limit to first 5
        except Exception:
            pass
        
        # Try to get LangChain version
        version = None
        try:
            import langchain
            version = getattr(langchain, "__version__", None)
            confidence += 0.1
        except ImportError:
            pass
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        return FrameworkInfo(
            framework_type=FrameworkType.LANGCHAIN,
            version=version,
            confidence=confidence,
            detected_modules=detected_modules,
            agent_class=agent_class
        )
    
    def normalize_trace_data(self, raw_trace_data: Dict[str, Any], 
                           framework_type: FrameworkType) -> NormalizedTrace:
        """
        Convert LangChain-specific trace data to normalized format.
        
        Args:
            raw_trace_data: Raw trace data from LangChain execution
            framework_type: Framework type (should be LANGCHAIN)
            
        Returns:
            Normalized trace data optimized for LangChain analysis
        """
        # Extract LangChain-specific execution steps
        execution_steps = []
        for step in raw_trace_data.get("steps", []):
            normalized_step = {
                "step_id": step.get("step_id", ""),
                "step_name": step.get("step_name", ""),
                "step_type": self._classify_langchain_step(step),
                "duration_ms": step.get("duration_ms", 0),
                "input_data": step.get("step_data", {}),
                "output_data": {},
                "metadata": step.get("metadata", {}),
                "success": step.get("error") is None
            }
            
            # Add LangChain-specific metadata
            if "chain" in step.get("step_name", "").lower():
                normalized_step["langchain_component"] = "chain"
            elif "llm" in step.get("step_name", "").lower():
                normalized_step["langchain_component"] = "llm"
            elif "memory" in step.get("step_name", "").lower():
                normalized_step["langchain_component"] = "memory"
            elif "tool" in step.get("step_name", "").lower():
                normalized_step["langchain_component"] = "tool"
            
            execution_steps.append(normalized_step)
        
        # Extract performance metrics
        performance_metrics = {
            "total_duration_ms": raw_trace_data.get("duration_ms", 0),
            "memory_usage_mb": raw_trace_data.get("memory_growth_mb", 0),
            "step_count": len(execution_steps),
            "chain_depth": self._calculate_chain_depth(execution_steps),
            "llm_call_count": self._count_llm_calls(execution_steps),
            "tool_usage_count": self._count_tool_usage(execution_steps)
        }
        
        # Organize LangChain-specific data
        framework_specific_data = {
            "original_trace": raw_trace_data,
            "langchain_components": self._analyze_langchain_components(raw_trace_data),
            "chain_analysis": self._analyze_chain_structure(execution_steps),
            "llm_analysis": self._analyze_llm_usage(execution_steps),
            "memory_analysis": self._analyze_memory_usage(execution_steps),
            "performance_insights": self._generate_langchain_insights(performance_metrics, execution_steps)
        }
        
        # Create metadata
        metadata = {
            "framework_version": self._get_langchain_version(),
            "agent_type": raw_trace_data.get("function_name", "unknown"),
            "environment": raw_trace_data.get("environment", "unknown"),
            "normalized_by": "langchain_adapter",
            "normalization_timestamp": raw_trace_data.get("collected_at"),
            "complexity_score": self._calculate_complexity_score(execution_steps)
        }
        
        return NormalizedTrace(
            trace_id=raw_trace_data.get("trace_id", "unknown"),
            framework_type=framework_type.value,
            agent_type=raw_trace_data.get("function_name", "langchain_agent"),
            execution_steps=execution_steps,
            performance_metrics=performance_metrics,
            framework_specific_data=framework_specific_data,
            metadata=metadata
        )
    
    def get_framework_hooks(self) -> Dict[str, Any]:
        """
        Get LangChain-specific hooks for instrumenting execution.
        
        Returns:
            Dictionary of LangChain hook functions and configuration
        """
        return {
            "chain_hooks": {
                "pre_run": self._hook_chain_pre_run,
                "post_run": self._hook_chain_post_run,
                "step_run": self._hook_chain_step
            },
            "llm_hooks": {
                "pre_call": self._hook_llm_pre_call,
                "post_call": self._hook_llm_post_call,
                "token_usage": self._hook_token_usage
            },
            "memory_hooks": {
                "memory_save": self._hook_memory_save,
                "memory_load": self._hook_memory_load,
                "memory_clear": self._hook_memory_clear
            },
            "tool_hooks": {
                "tool_start": self._hook_tool_start,
                "tool_end": self._hook_tool_end,
                "tool_error": self._hook_tool_error
            }
        }
    
    def hook_chain_execution(self, chain: Any, callbacks: Optional[List] = None) -> Any:
        """
        Hook into LangChain chain execution for step-by-step tracing.
        
        Args:
            chain: LangChain chain instance to hook
            callbacks: Optional existing callbacks to preserve
            
        Returns:
            Hooked chain with debugging capabilities
        """
        # Try to add our custom callback for tracing
        try:
            from langchain.callbacks.base import BaseCallbackHandler
            
            class DebugCallbackHandler(BaseCallbackHandler):
                def __init__(self, adapter_instance):
                    self.adapter = adapter_instance
                
                def on_chain_start(self, serialized, inputs, **kwargs):
                    self.adapter._hook_chain_pre_run(serialized, inputs)
                
                def on_chain_end(self, outputs, **kwargs):
                    self.adapter._hook_chain_post_run(outputs)
                
                def on_llm_start(self, serialized, prompts, **kwargs):
                    self.adapter._hook_llm_pre_call(serialized, prompts)
                
                def on_llm_end(self, response, **kwargs):
                    self.adapter._hook_llm_post_call(response)
            
            # Add our callback to the chain
            debug_callback = DebugCallbackHandler(self)
            if hasattr(chain, 'callbacks'):
                if chain.callbacks is None:
                    chain.callbacks = []
                chain.callbacks.append(debug_callback)
            
        except ImportError:
            # LangChain not available or different version
            pass
        
        return chain
    
    def capture_llm_calls(self, llm_instance: Any) -> Any:
        """
        Wrap LLM instance to capture API calls with tokens, cost, and timing.
        
        Args:
            llm_instance: LangChain LLM instance
            
        Returns:
            Wrapped LLM with debugging capabilities
        """
        # Store original methods
        if hasattr(llm_instance, '_call'):
            original_call = llm_instance._call
            
            def traced_call(prompt: str, stop: Optional[List[str]] = None, **kwargs):
                self._hook_llm_pre_call({"llm_type": type(llm_instance).__name__}, [prompt])
                
                try:
                    result = original_call(prompt, stop, **kwargs)
                    self._hook_llm_post_call({"text": result})
                    return result
                except Exception as e:
                    self._hook_llm_error(e)
                    raise
            
            llm_instance._call = traced_call
        
        return llm_instance
    
    def trace_memory_usage(self, memory_instance: Any) -> Dict[str, Any]:
        """
        Monitor and trace LangChain conversation memory consumption.
        
        Args:
            memory_instance: LangChain memory instance
            
        Returns:
            Memory metrics and insights
        """
        memory_metrics = {
            "memory_type": type(memory_instance).__name__,
            "memory_size": 0,
            "message_count": 0,
            "token_estimate": 0
        }
        
        try:
            # Try to get memory buffer content
            if hasattr(memory_instance, 'buffer'):
                buffer_content = str(memory_instance.buffer)
                memory_metrics["memory_size"] = len(buffer_content)
                memory_metrics["token_estimate"] = len(buffer_content.split()) * 1.3  # Rough estimate
            
            # Try to get chat messages
            if hasattr(memory_instance, 'chat_memory') and hasattr(memory_instance.chat_memory, 'messages'):
                messages = memory_instance.chat_memory.messages
                memory_metrics["message_count"] = len(messages)
                
                # Estimate tokens from messages
                total_content = ""
                for msg in messages:
                    if hasattr(msg, 'content'):
                        total_content += str(msg.content)
                
                memory_metrics["token_estimate"] = len(total_content.split()) * 1.3
                memory_metrics["memory_size"] = len(total_content)
        
        except Exception:
            # Memory introspection failed, use defaults
            pass
        
        return memory_metrics
    
    def _classify_langchain_step(self, step: Dict[str, Any]) -> str:
        """Classify a step as a specific LangChain operation type."""
        step_name = step.get("step_name", "").lower()
        
        if "chain" in step_name:
            return "chain_execution"
        elif any(keyword in step_name for keyword in ["llm", "openai", "anthropic", "huggingface"]):
            return "llm_call"
        elif "memory" in step_name:
            return "memory_operation"
        elif "tool" in step_name:
            return "tool_execution"
        elif "retriever" in step_name:
            return "retrieval_operation"
        elif "prompt" in step_name:
            return "prompt_processing"
        else:
            return "generic_operation"
    
    def _calculate_chain_depth(self, execution_steps: List[Dict[str, Any]]) -> int:
        """Calculate the maximum chain depth from execution steps."""
        max_depth = 0
        current_depth = 0
        
        for step in execution_steps:
            if step.get("langchain_component") == "chain":
                if "start" in step.get("step_name", "").lower():
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif "end" in step.get("step_name", "").lower():
                    current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def _count_llm_calls(self, execution_steps: List[Dict[str, Any]]) -> int:
        """Count the number of LLM API calls in the execution."""
        return len([step for step in execution_steps 
                   if step.get("step_type") == "llm_call"])
    
    def _count_tool_usage(self, execution_steps: List[Dict[str, Any]]) -> int:
        """Count the number of tool executions."""
        return len([step for step in execution_steps 
                   if step.get("step_type") == "tool_execution"])
    
    def _analyze_langchain_components(self, raw_trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze LangChain components used in the execution."""
        return {
            "detected_chains": [],
            "detected_llms": [],
            "detected_tools": [],
            "detected_memory": [],
            "component_interaction_map": {}
        }
    
    def _analyze_chain_structure(self, execution_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the structure and flow of LangChain chains."""
        chain_steps = [step for step in execution_steps 
                      if step.get("langchain_component") == "chain"]
        
        return {
            "chain_count": len(set(step.get("step_name") for step in chain_steps)),
            "average_chain_duration": sum(step.get("duration_ms", 0) for step in chain_steps) / max(len(chain_steps), 1),
            "chain_success_rate": len([step for step in chain_steps if step.get("success", True)]) / max(len(chain_steps), 1),
            "bottleneck_chains": []  # To be populated with performance analysis
        }
    
    def _analyze_llm_usage(self, execution_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze LLM usage patterns and performance."""
        llm_steps = [step for step in execution_steps 
                    if step.get("step_type") == "llm_call"]
        
        if not llm_steps:
            return {"llm_calls": 0}
        
        total_duration = sum(step.get("duration_ms", 0) for step in llm_steps)
        
        return {
            "llm_calls": len(llm_steps),
            "total_llm_time_ms": total_duration,
            "average_llm_time_ms": total_duration / len(llm_steps),
            "llm_time_percentage": 0,  # To be calculated against total execution time
            "failed_llm_calls": len([step for step in llm_steps if not step.get("success", True)]),
            "llm_models_used": list(set(step.get("metadata", {}).get("model") for step in llm_steps if step.get("metadata", {}).get("model")))
        }
    
    def _analyze_memory_usage(self, execution_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze memory system usage and patterns."""
        memory_steps = [step for step in execution_steps 
                       if step.get("langchain_component") == "memory"]
        
        return {
            "memory_operations": len(memory_steps),
            "memory_saves": len([step for step in memory_steps if "save" in step.get("step_name", "").lower()]),
            "memory_loads": len([step for step in memory_steps if "load" in step.get("step_name", "").lower()]),
            "memory_efficiency_score": 1.0 if memory_steps else 0.0  # Placeholder for actual calculation
        }
    
    def _generate_langchain_insights(self, performance_metrics: Dict[str, Any], 
                                   execution_steps: List[Dict[str, Any]]) -> List[str]:
        """Generate LangChain-specific performance insights."""
        insights = []
        
        # LLM call optimization insights
        llm_call_count = performance_metrics.get("llm_call_count", 0)
        if llm_call_count > 5:
            insights.append(f"High number of LLM calls ({llm_call_count}) - consider batching or caching")
        
        # Chain depth insights
        chain_depth = performance_metrics.get("chain_depth", 0)
        if chain_depth > 3:
            insights.append(f"Deep chain nesting ({chain_depth} levels) may impact performance")
        
        # Tool usage insights
        tool_count = performance_metrics.get("tool_usage_count", 0)
        if tool_count > 10:
            insights.append(f"Heavy tool usage ({tool_count} calls) - monitor for bottlenecks")
        
        # Memory insights
        total_duration = performance_metrics.get("total_duration_ms", 0)
        if total_duration > 30000:  # 30 seconds
            insights.append("Long execution time - consider async processing or streaming")
        
        return insights
    
    def _calculate_complexity_score(self, execution_steps: List[Dict[str, Any]]) -> float:
        """Calculate a complexity score for the LangChain execution."""
        if not execution_steps:
            return 0.0
        
        score = 0.0
        
        # Base score from number of steps
        score += len(execution_steps) * 0.1
        
        # Add complexity for different component types
        component_types = set(step.get("langchain_component") for step in execution_steps)
        score += len(component_types) * 0.5
        
        # Add complexity for failed steps
        failed_steps = len([step for step in execution_steps if not step.get("success", True)])
        score += failed_steps * 1.0
        
        # Normalize to 0-10 scale
        return min(score, 10.0)
    
    def _get_langchain_version(self) -> Optional[str]:
        """Get the LangChain version if available."""
        try:
            import langchain
            return getattr(langchain, "__version__", None)
        except ImportError:
            return None
    
    # Hook methods for LangChain instrumentation
    def _hook_chain_pre_run(self, serialized: Dict[str, Any], inputs: Dict[str, Any]) -> None:
        """Hook called before chain execution."""
        # Log chain start with inputs
        pass
    
    def _hook_chain_post_run(self, outputs: Dict[str, Any]) -> None:
        """Hook called after chain execution."""
        # Log chain completion with outputs
        pass
    
    def _hook_chain_step(self, step_info: Dict[str, Any]) -> None:
        """Hook called for each chain step."""
        # Log individual chain step
        pass
    
    def _hook_llm_pre_call(self, serialized: Dict[str, Any], prompts: List[str]) -> None:
        """Hook called before LLM API call."""
        # Log LLM call start with prompt info
        pass
    
    def _hook_llm_post_call(self, response: Dict[str, Any]) -> None:
        """Hook called after LLM API call."""
        # Log LLM response with token usage
        pass
    
    def _hook_llm_error(self, error: Exception) -> None:
        """Hook called when LLM call fails."""
        # Log LLM error
        pass
    
    def _hook_token_usage(self, usage_info: Dict[str, Any]) -> None:
        """Hook for tracking token usage and costs."""
        # Log token usage and cost information
        pass
    
    def _hook_memory_save(self, memory_data: Dict[str, Any]) -> None:
        """Hook called when memory is saved."""
        # Log memory save operation
        pass
    
    def _hook_memory_load(self, memory_data: Dict[str, Any]) -> None:
        """Hook called when memory is loaded."""
        # Log memory load operation
        pass
    
    def _hook_memory_clear(self) -> None:
        """Hook called when memory is cleared."""
        # Log memory clear operation
        pass
    
    def _hook_tool_start(self, tool_info: Dict[str, Any]) -> None:
        """Hook called when tool execution starts."""
        # Log tool execution start
        pass
    
    def _hook_tool_end(self, tool_result: Dict[str, Any]) -> None:
        """Hook called when tool execution ends."""
        # Log tool execution completion
        pass
    
    def _hook_tool_error(self, error: Exception) -> None:
        """Hook called when tool execution fails."""
        # Log tool execution error
        pass