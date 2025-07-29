#!/usr/bin/env python3
"""
Command-line interface for Mammo-CLIP inference
"""

import argparse
import json
import sys
from pathlib import Path
from .inference import MammoClipModel


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Mammo-CLIP: Zero-shot mammography analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic inference with HuggingFace model (automatic download)
  mammoclip-inference --image mammogram.dcm
  
  # With custom local checkpoint
  mammoclip-inference --image mammogram.dcm --checkpoint model.tar
  
  # Custom prompts from JSON file
  mammoclip-inference --image mammogram.dcm --prompts custom_prompts.json
  
  # Output results to JSON file
  mammoclip-inference --image mammogram.dcm --output results.json
  
  # Use different model variant
  mammoclip-inference --image mammogram.dcm --model-name efficientnet_b5
        """
    )
    
    parser.add_argument(
        "--image", 
        type=str, 
        required=True, 
        help="Path to DICOM image file"
    )
    parser.add_argument(
        "--checkpoint", 
        type=str, 
        help="Path to model checkpoint (.tar file, optional - will download from HuggingFace if not provided)"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="efficientnet_b5",
        help="Name of the pretrained model to use (default: efficientnet_b5)"
    )
    parser.add_argument(
        "--prompts", 
        type=str, 
        help="JSON file with custom prompts (optional)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        help="Output JSON file path (optional, prints to stdout if not specified)"
    )
    parser.add_argument(
        "--device", 
        type=str, 
        help="Device to use: 'cpu', 'cuda', or 'auto' (default: auto)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.image).exists():
        print(f"Error: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)
    
    if args.checkpoint and not Path(args.checkpoint).exists():
        print(f"Error: Checkpoint file not found: {args.checkpoint}", file=sys.stderr)
        sys.exit(1)
    
    # Default prompts (same as in the original inference script)
    default_prompts = {
        "mass": [
            "no mass",
            "mass"
        ],
        "suspicious_calcification": [
            "no suspicious calcification", 
            "suspicious calcification"
        ],
        "malignancy": [
            "no malignancy",
            "malignancy"
        ],
        "density": [
            "fatty",
            "scattered areas of fibroglandular density",
            "heterogeneously dense",
            "extremely dense"
        ]
    }
    
    # Load custom prompts if provided
    if args.prompts:
        if not Path(args.prompts).exists():
            print(f"Error: Prompts file not found: {args.prompts}", file=sys.stderr)
            sys.exit(1)
        
        try:
            with open(args.prompts, 'r') as f:
                prompts_dict = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in prompts file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        prompts_dict = default_prompts
    
    try:
        # Initialize inference model
        if args.checkpoint:
            print(f"Loading Mammo-CLIP model from {args.checkpoint}...")
            inferencer = MammoClipModel(args.checkpoint, device=args.device)
        else:
            print(f"Loading Mammo-CLIP model: {args.model_name} (will download from HuggingFace)...")
            inferencer = MammoClipModel(model_name=args.model_name, device=args.device)
        
        # Run inference
        print(f"Running inference on: {args.image}")
        results = inferencer.predict(args.image, prompts_dict)
        
        # Prepare output
        output_data = {
            "image_path": str(args.image),
            "checkpoint_path": str(args.checkpoint) if args.checkpoint else None,
            "model_name": args.model_name,
            "results": results
        }
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"Results saved to: {args.output}")
        else:
            print(json.dumps(output_data, indent=2))
        
        # Print summary to stderr so it doesn't interfere with JSON output
        print("\n" + "="*60, file=sys.stderr)
        print("INFERENCE SUMMARY", file=sys.stderr)
        print("="*60, file=sys.stderr)
        for category, result in results.items():
            print(f"{category.upper()}: {result['prediction']} (confidence: {result['confidence']:.4f})", file=sys.stderr)
        
    except Exception as e:
        print(f"Error during inference: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 