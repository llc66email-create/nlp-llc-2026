"""
Story Weaver 初始化脚本 - 设置项目和数据
"""
import os
from pathlib import Path
import json

def initialize_project():
    """初始化项目结构和数据"""
    print("=" * 60)
    print("Story Weaver 项目初始化")
    print("=" * 60)
    
    # 创建目录
    print("\n1. 创建目录结构...")
    dirs = [
        'data/knowledge_base',
        'story_weaver/nlu',
        'story_weaver/state_management',
        'story_weaver/rag',
        'story_weaver/nlg',
        'story_weaver/consistency',
        'story_weaver/logging',
        'web_interface/templates',
        'web_interface/static/css',
        'web_interface/static/js',
        'logs',
        'tests'
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {d}")
    
    # 创建空的__init__.py
    print("\n2. 创建模块初始化文件...")
    init_files = [
        'story_weaver/__init__.py',
        'story_weaver/nlu/__init__.py',
        'story_weaver/state_management/__init__.py',
        'story_weaver/rag/__init__.py',
        'story_weaver/nlg/__init__.py',
        'story_weaver/consistency/__init__.py',
        'tests/__init__.py'
    ]
    
    for f in init_files:
        Path(f).touch(exist_ok=True)
        print(f"   ✓ {f}")
    
    # 验证关键文件
    print("\n3. 验证关键文件...")
    key_files = [
        'config.py',
        'app.py',
        'requirements.txt',
        'data/knowledge_base/plot_segments.json',
        'data/knowledge_base/character_graph.json',
        'data/knowledge_base/consistency_rules.json',
        'data/knowledge_base/world_state.json',
        'story_weaver/nlu/intent_extractor.py',
        'story_weaver/state_management/game_state.py',
        'story_weaver/rag/retriever.py',
        'story_weaver/nlg/generator.py',
        'story_weaver/consistency/checker.py',
        'story_weaver/logging/__init__.py',
        'story_weaver/core.py',
        'web_interface/templates/index.html',
        'web_interface/static/css/style.css',
        'web_interface/static/js/main.js'
    ]
    
    missing_files = []
    for f in key_files:
        if os.path.exists(f):
            print(f"   ✓ {f}")
        else:
            print(f"   ✗ {f} (缺失)")
            missing_files.append(f)
    
    if missing_files:
        print(f"\n⚠️  警告: 缺失 {len(missing_files)} 个文件")
        print("请确保所有源文件已正确创建")
        return False
    
    print("\n" + "=" * 60)
    print("项目初始化完成！")
    print("=" * 60)
    
    print("\n📖 后续步骤:")
    print("1. 安装依赖: pip install -r requirements.txt")
    print("2. 启动Web服务: python app.py")
    print("3. 访问界面: http://localhost:5000")
    
    return True

def check_dependencies():
    """检查依赖"""
    print("\n检查依赖...")
    
    try:
        import torch
        print(f"   ✓ torch {torch.__version__}")
    except ImportError:
        print("   ✗ torch 未安装")
    
    try:
        import transformers
        print(f"   ✓ transformers {transformers.__version__}")
    except ImportError:
        print("   ✗ transformers 未安装")
    
    try:
        import flask
        print(f"   ✓ flask {flask.__version__}")
    except ImportError:
        print("   ✗ flask 未安装")
    
    try:
        import sentence_transformers
        print(f"   ✓ sentence-transformers {sentence_transformers.__version__}")
    except ImportError:
        print("   ✗ sentence-transformers 未安装")
    
    try:
        import faiss
        print(f"   ✓ faiss")
    except ImportError:
        print("   ✗ faiss 未安装")
    
    try:
        import nltk
        print(f"   ✓ nltk {nltk.__version__}")
    except ImportError:
        print("   ✗ nltk 未安装")

if __name__ == "__main__":
    import sys
    
    success = initialize_project()
    check_dependencies()
    
    sys.exit(0 if success else 1)
