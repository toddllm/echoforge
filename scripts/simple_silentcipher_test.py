#!/usr/bin/env python3
"""
A minimal test script for silentcipher.
"""

import torch
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

def main():
    try:
        import silentcipher
        logger.info(f"Successfully imported silentcipher version: {getattr(silentcipher, '__version__', 'unknown')}")
        logger.info(f"Available attributes: {dir(silentcipher)}")
        
        # Explore the model module
        if hasattr(silentcipher, "model"):
            logger.info("Found silentcipher.model, exploring its contents")
            logger.info(f"Model module attributes: {dir(silentcipher.model)}")
            
            # Check if it has a TTSModel or similar
            if hasattr(silentcipher.model, "TTSModel"):
                logger.info("Found TTSModel in silentcipher.model")
                
                try:
                    # Try to initialize the model
                    tts_model = silentcipher.model.TTSModel()
                    logger.info(f"Successfully initialized TTSModel: {tts_model}")
                    logger.info(f"TTSModel attributes: {dir(tts_model)}")
                    
                    # Try to generate speech
                    text = "This is a simple test of the silentcipher package."
                    if hasattr(tts_model, "generate") or hasattr(tts_model, "synthesize"):
                        method = getattr(tts_model, "generate", None) or getattr(tts_model, "synthesize", None)
                        logger.info(f"Using {method.__name__} method")
                        
                        audio = method(text)
                        logger.info(f"Generated audio: {audio}")
                        return True
                    else:
                        logger.warning("TTSModel doesn't have generate or synthesize method")
                except Exception as e:
                    logger.error(f"Error with TTSModel: {e}")
            
            # Look for any other useful classes in the model module
            for attr_name in dir(silentcipher.model):
                attr = getattr(silentcipher.model, attr_name)
                if isinstance(attr, type):  # If it's a class
                    logger.info(f"Found class: {attr_name}")
                    
                    # Check if it has any promising methods
                    class_methods = [method for method in dir(attr) if not method.startswith('_')]
                    speech_related_methods = [method for method in class_methods if 
                                          any(keyword in method.lower() for keyword in 
                                              ['speech', 'generate', 'synthesize', 'audio', 'voice'])]
                    
                    if speech_related_methods:
                        logger.info(f"Class {attr_name} has promising methods: {speech_related_methods}")
        
        # Try a more direct approach with searching for any TTS-related functionality
        text = "This is a simple test of the silentcipher package."
        
        # Check all modules and attributes for anything TTS-related
        for module_name in dir(silentcipher):
            if module_name.startswith('__'):
                continue
                
            try:
                module = getattr(silentcipher, module_name)
                logger.info(f"Exploring module: {module_name}")
                
                # Look for TTS-related attributes
                tts_attributes = [attr for attr in dir(module) if 
                              any(keyword in attr.lower() for keyword in 
                                  ['tts', 'text_to_speech', 'speech', 'generate', 'synthesize'])]
                
                if tts_attributes:
                    logger.info(f"Found TTS-related attributes in {module_name}: {tts_attributes}")
                    
                    # Try each attribute
                    for attr_name in tts_attributes:
                        try:
                            attr = getattr(module, attr_name)
                            logger.info(f"Examining attribute: {attr_name}, type: {type(attr)}")
                            
                            # If it's a callable, try calling it
                            if callable(attr):
                                logger.info(f"Trying to call {attr_name}")
                                result = attr(text)
                                logger.info(f"Result from {attr_name}: {result}")
                                return True
                        except Exception as e:
                            logger.warning(f"Error with {attr_name}: {e}")
            except Exception as e:
                logger.warning(f"Error exploring module {module_name}: {e}")
        
        logger.error("No TTS functionality found in silentcipher")
        return False
            
    except ImportError as e:
        logger.error(f"Could not import silentcipher: {e}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
        
if __name__ == "__main__":
    success = main()
    if success:
        print("Test completed successfully")
    else:
        print("Test failed") 