#!/usr/bin/env python3
"""
Story Weaver 系统验证脚本
检查所有组件是否正确配置
"""

import os
import sys
from pathlib import Path

def check_environment():
    """检查环境"""
    print("=" * 60)
    print("Story Weaver - 系统验证")
    print("=" * 60)
    
    checks = []
    
    # 检查Python版本
    print(f"\n✓ Python版本: {sys.version}")
    
    # 检查目录结构
    print("\n检查目录结构...")
    required_dirs = [
        "data/knowledge_base",
        "story_weaver/nlu",
        "story_weaver/state_management",
        "story_weaver/rag",
        "story_weaver/nlg",
        "story_weaver/consistency",
        "story_weaver/logging",
        "web_interface/templates",
        "web_interface/static/css",
        "web_interface/static/js",
        "logs"
    ]
    
    for d in required_dirs:
        exists = Path(d).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {d}")
        checks.append(exists)
    
    # 检查关键文件
    print("\n检查关键文件...")
    required_files = [
        "config.py",
        "app.py",
        "story_weaver/core.py",
        "story_weaver/nlu/intent_extractor.py",
        "story_weaver/state_management/game_state.py",
        "story_weaver/rag/retriever.py",
        "story_weaver/nlg/generator.py",
        "story_weaver/consistency/checker.py",
        "data/knowledge_base/plot_segments.json",
        "data/knowledge_base/character_graph.json",
        "data/knowledge_base/consistency_rules.json",
        "web_interface/templates/index.html",
        "requirements.txt",
        "README.md"
    ]
    
    for f in required_files:
        exists = Path(f).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {f}")
        checks.append(exists)
    
    # 检查依赖
    print("\n检查Python依赖...")
    optional_packages = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("sentence_transformers", "Sentence Transformers"),
        ("flask", "Flask"),
        ("nltk", "NLTK"),
    ]
    
    optional_packages_available = 0
    for package, name in optional_packages:
        try:
            __import__(package)
            print(f"  ✓ {name} 已安装")
            optional_packages_available += 1
        except ImportError:
            print(f"  ✗ {name} 未安装 - 运行: pip install -r requirements.txt")
    
    print(f"\n依赖检查: {optional_packages_available}/{len(optional_packages)} 已安装")
    
    # 总结
    print("\n" + "=" * 60)
    all_passed = all(checks)
    
    if all_passed:
        print("✅ 系统验证通过！")
        print("\n后续步骤:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 启动服务: python app.py")
        print("3. 访问: http://localhost:5000")
        return 0
    else:
        print("⚠️ 系统验证发现问题")
        print(f"成功: {sum(checks)}/{len(checks)}")
        print("\n请运行 python init_project.py 完成初始化")
        return 1

def show_file_structure():
    """显示文件结构"""
    print("\n文件结构:")
    print("""
nlp2026/
├── 📄 config.py                           (配置文件)
├── 📄 app.py                              (Flask应用)  
├── 📄 story_weaver/core.py                (核心系统)
├── 📄 requirements.txt                    (依赖)
├── 📄 test_system.py                      (测试脚本)
├── 📄 init_project.py                     (初始化脚本)
│
├── 📁 story_weaver/                       (主模块)
│   ├── nlu/intent_extractor.py            (意图识别)
│   ├── state_management/game_state.py     (状态管理)
│   ├── rag/retriever.py                   (RAG检索)
│   ├── nlg/generator.py                   (文本生成)
│   ├── consistency/checker.py             (一致性检查)
│   └── logging/__init__.py                (日志系统)
│
├── 📁 data/knowledge_base/                (知识库)
│   ├── plot_segments.json                 (13个情节片段)
│   ├── character_graph.json               (7个角色)
│   ├── consistency_rules.json             (10条规则)
│   └── world_state.json                   (世界定义)
│
├── 📁 web_interface/                      (Web界面)
│   ├── templates/index.html               (页面)
│   └── static/
│       ├── css/style.css                  (样式)
│       └── js/main.js                     (脚本)
│
└── 📄 README.md, QUICKSTART.md            (文档)
    """)

if __name__ == "__main__":
    result = check_environment()
    show_file_structure()
    sys.exit(result)
