#!/usr/bin/env python3
"""
n8n Workflow URL Fixer
Repariert relative URLs in n8n Workflows zu absoluten URLs
"""

import json
import os
import sys
from pathlib import Path

def fix_workflow_urls(workflow_path: str, base_url: str = "http://localhost:8000") -> bool:
    """Fix URLs in a single workflow file"""
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        modified = False
        
        # Fix nodes
        for node in workflow.get('nodes', []):
            if node.get('type') == 'n8n-nodes-base.httpRequest':
                params = node.get('parameters', {})
                url = params.get('url', '')
                
                # Fix relative URLs
                if url.startswith('/'):
                    params['url'] = f"{base_url}{url}"
                    modified = True
                    print(f"  Fixed: {url} → {params['url']}")
                
                # Remove problematic options
                if 'options' in params:
                    options = params['options']
                    if 'timeout' in options:
                        del options['timeout']
                        modified = True
                        print(f"  Removed timeout option")
                
                # Ensure method is set
                if 'method' not in params and 'url' in params:
                    params['method'] = 'GET'
                    modified = True
                    print(f"  Added method: GET")
        
        # Update version
        workflow['version'] = 'v5-fixed-abs-urls'
        modified = True
        
        if modified:
            with open(workflow_path, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2, ensure_ascii=False)
            print(f"✅ Fixed: {workflow_path}")
            return True
        else:
            print(f"ℹ️  No changes needed: {workflow_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {workflow_path}: {e}")
        return False

def main():
    """Main function"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    workflows_dir = project_root / "integrations" / "n8n" / "workflows"
    
    if not workflows_dir.exists():
        print(f"❌ Workflows directory not found: {workflows_dir}")
        sys.exit(1)
    
    workflow_files = [
        "rico_v5_event_hub.json",
        "rico_v5_autopilot.json"
    ]
    
    print("🔧 n8n Workflow URL Fixer")
    print("=" * 40)
    
    fixed_count = 0
    for filename in workflow_files:
        workflow_path = workflows_dir / filename
        if workflow_path.exists():
            print(f"\n📁 Processing: {filename}")
            if fix_workflow_urls(str(workflow_path)):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {workflow_path}")
    
    print(f"\n🎯 Summary: {fixed_count}/{len(workflow_files)} files fixed")
    
    if fixed_count > 0:
        print("\n✅ All workflows are now n8n v1.x compatible!")
        print("   - Absolute URLs set")
        print("   - Problematic options removed")
        print("   - Version updated")
    else:
        print("\nℹ️  No fixes needed - workflows are already compatible")

if __name__ == "__main__":
    main()
