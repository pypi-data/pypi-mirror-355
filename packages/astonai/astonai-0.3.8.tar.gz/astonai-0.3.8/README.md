# Aston AI

Aston is a code intelligence system for parsing, analyzing, and finding test coverage gaps in your code.

> **Latest**: v0.3.7 has astonrank (go) to aid criticality scoring

```bash
# Quick Setup
pip install astonai
aston init --offline
aston graph build
aston cache warm-up  # Enable high-performance caching

# Key Features
aston coverage --critical-path        # Find high-impact code paths
aston test-suggest core/auth.py --k 3 # Generate test suggestions
aston criticality analyze --top 10    # Identify critical components
aston regression-guard --since HEAD~1 # Analyze change risk
```

## Feature Overview

| Version | Feature | Key Benefits | CLI Commands |
|---------|---------|--------------|-------------|
| **v0.3.8** | **Local Embeddings** | • Local MiniLM embedding generation<br>• FAISS vector similarity search<br>• No external API dependencies<br>• Repository-centric storage | `aston embed --backend minilm`<br>`aston embed --dry-run`<br>`aston embed --file src/main.py` |
| **v0.3.4** | **Micro Cache** | • Sub-300ms graph operations<br>• 256MB memory limit<br>• Performance monitoring | `aston cache warm-up`<br>`aston cache status`<br>`aston cache clear` |
| **v0.3.3** | **Criticality Scorer** | • Advanced risk assessment<br>• Component importance ranking<br>• Test prioritization | `aston criticality analyze`<br>`aston criticality export`<br>`aston criticality tune` |
| **v0.3.2** | **Regression Guard** | • Multi-factor risk scoring<br>• Threshold-based blocking<br>• CI/CD integration | `aston regression-guard --since <ref>`<br>`aston regression-guard --exit-code` |
| **v0.2.5** | **Test Suggestions** | • Intelligent pytest generation<br>• LLM fallback mode<br>• Rich context for developers | `aston test-suggest <file> --k 3`<br>`aston test-suggest <file> --prompt`<br>`aston test-suggest <file> --llm` |
| **v0.2.3** | **Filter Engine** | • Incremental rechunk<br>• Smart change detection<br>• Pattern-based filtering | `aston init --rechunk`<br>`aston refresh`<br>`aston init --preset python-only` |
| **v0.2.0** | **Critical Path** | • High-impact node detection<br>• Focus testing efforts<br>• Weight-based scoring | `aston coverage --critical-path`<br>`aston coverage --weight loc` |
| **v0.1.19** | **Graph Visualization** | • DOT format export<br>• Interactive visualization<br>• Relationship exploration | `aston graph export`<br>`aston graph view` |
| **v0.1.18** | **Relationship Analysis** | • Function call tracking<br>• Import dependency mapping<br>• Graph statistics | `aston graph build`<br>`aston graph stats` |
| **v0.1.16** | **Core CLI** | • Repository initialization<br>• Coverage gap detection<br>• Test execution | `aston init`<br>`aston coverage`<br>`aston test` |

# Explain
aston init → creates chunks + nodes
aston graph build → uses those to create edges

## Installation

```bash
# Base installation (fast, minimal dependencies)
pip install astonai

# For database features (Neo4j graph storage)
pip install "astonai[db]"

# For visualization features (matplotlib plotting)
pip install "astonai[viz]"

# For LLM-powered features (OpenAI integration)
pip install "astonai[llm]"

# For local embedding features (MiniLM + FAISS)
pip install "astonai[embed]"

# Everything bundle
pip install "astonai[all]"

# Quiet installation (suppress download chatter)
pip install -q astonai
```

**Installation Notes:**
- **Base install**: Core functionality with offline mode (10 dependencies, ~20-25 packages)
- **Database extra**: Adds Neo4j for live graph storage when not using `--offline` mode
- **Visualization extra**: Adds matplotlib for graph plotting and visualization features
- **LLM extra**: Adds OpenAI client for advanced test suggestion capabilities
- **Embed extra**: Adds sentence-transformers and FAISS for local embedding generation
- **Version checking**: Run `aston --version` to verify installation

## Quick Start

```bash
# Initialize your repository
aston init --offline

# Generate knowledge graph relationships
aston graph build

# View knowledge graph statistics
aston graph stats

# Smart incremental updates (recommended for ongoing development)
aston refresh

# Enable high-performance caching
aston cache warm-up
aston cache status

# Find critical paths and generate test suggestions
aston coverage --critical-path
aston test-suggest core/auth.py --k 3
aston test-suggest user/models.py --prompt --yaml context.yaml

# Analyze code criticality and regression risk
aston criticality analyze --top 10
aston regression-guard --since HEAD~1
```

## Core Commands

### Repository Initialization

```bash
# Initialize repository and create knowledge graph
aston init [--offline] [--preset PRESET] [--include PATTERN] [--exclude PATTERN]

# Incremental rechunk - fast updates for changed files only
aston init --rechunk [--offline]

# Force full rebuild
aston init --force [--offline]
```

**Advanced Filtering Options:**
- `--preset`: Apply preset configurations (`python-only`, `no-tests`, `source-only`, `minimal`)
- `--include`, `-i`: Include only files matching these glob patterns (can be used multiple times)
- `--exclude`, `-e`: Exclude files matching these glob patterns in addition to defaults (can be used multiple times)
- `--include-regex`: Include only files matching these regex patterns (can be used multiple times)
- `--exclude-regex`: Exclude files matching these regex patterns (can be used multiple times)
- `--dry-run`: Show which files would be processed without actually processing them
- `--show-patterns`: Display all active filter patterns and exit
- `--create-astonignore`: Create a template .astonignore file for persistent filtering

**Incremental Updates:**
- `--rechunk`: Process only files that have changed since last run (fast incremental updates)
- `--force`: Force complete rebuild even if knowledge graph exists

**Default Excludes**: Common directories are automatically excluded:
- `venv*/**`, `.venv*/**`, `env/**`, `.env/**`
- `node_modules/**`, `.git/**`, `.svn/**`, `.hg/**`
- `__pycache__/**`, `*.pyc`, `.pytest_cache/**`
- `build/**`, `dist/**`, `*.egg-info/**`
- `.idea/**`, `.vscode/**`, and more

**Examples:**
```bash
# Use preset configurations
aston init --preset python-only --offline
aston init --preset no-tests --offline

# Incremental rechunk for fast updates
aston init --rechunk --offline

# Custom filtering with patterns
aston init --include "src/**/*.py" --include "lib/**/*.py" --offline
aston init --exclude "legacy/**" --exclude "deprecated/**" --offline

# Use regex patterns for advanced filtering
aston init --include-regex ".*/(core|utils)/.*\.py$" --offline

# Preview what would be processed
aston init --preset minimal --dry-run

# Create .astonignore template for persistent rules
aston init --create-astonignore
```

**Environment Variables:**
- `ASTON_INCLUDE_PATTERNS`: Comma-separated include patterns
- `ASTON_EXCLUDE_PATTERNS`: Comma-separated exclude patterns

### Intelligent Refresh

```bash
# Smart incremental updates with change analysis
aston refresh [--strategy auto|incremental|full] [--force-full] [--dry-run]
```

The `refresh` command provides intelligent updates:
- **Auto Strategy**: Automatically chooses between incremental and full refresh based on changes
- **Change Detection**: Uses file hashes to detect actual modifications
- **Dry Run**: Preview what would be updated without making changes
- **Force Full**: Override auto-detection and force complete rebuild

**Examples:**
```bash
# Smart refresh (recommended)
aston refresh

# Preview changes without applying
aston refresh --dry-run

# Force full refresh
aston refresh --force-full

# Use specific strategy
aston refresh --strategy incremental
```

### Test Coverage

```bash
# Run tests with coverage
aston test

# Find testing gaps
aston coverage [--threshold 80] [--json results.json] [--exit-on-gap]

# Identify critical implementation nodes
aston coverage --critical-path [--n 50] [--weight loc]
```

Options:
- `--threshold`: Minimum coverage percentage (default: 0)
- `--json`: Output results in JSON format
- `--exit-on-gap`: Return code 1 if gaps found (useful for CI)
- `--coverage-file`: Specify custom coverage file location
- `--critical-path`: Identify critical code paths that need testing
- `--n`: Number of critical nodes to return (default: 50)
- `--weight`: Weight function for critical path (loc, calls, churn)

### Knowledge Graph

```bash
# Build edge relationships between nodes with advanced filtering
aston graph build [--preset PRESET] [--include PATTERN] [--exclude PATTERN]

# View statistics about the knowledge graph
aston graph stats

# Export graph to DOT format
aston graph export [--output graph.dot] [--filter CALLS,IMPORTS] [--open]

# Open interactive graph viewer in browser
aston graph view [--filter CALLS,IMPORTS]
```


**Advanced Filtering for Graph Build:**
- `--preset`: Apply preset configurations (`python-only`, `no-tests`, `source-only`, `minimal`)
- `--include`, `-i`: Include only files matching these glob patterns (can be used multiple times)
- `--exclude`, `-e`: Exclude files matching these glob patterns in addition to defaults (can be used multiple times)
- `--include-regex`: Include only files matching these regex patterns (can be used multiple times)
- `--exclude-regex`: Exclude files matching these regex patterns (can be used multiple times)
- `--dry-run`: Show which files would be processed without actually processing them
- `--show-patterns`: Display all active filter patterns and exit

**Examples:**
```bash
# Build with preset filtering
aston graph build --preset no-tests

# Include only specific directories
aston graph build --include "src/**/*.py" --include "lib/**/*.py"

# Use regex patterns for advanced filtering
aston graph build --include-regex ".*/(core|utils)/.*\.py$"

# Preview what would be processed
aston graph build --preset python-only --dry-run
```

The graph command provides:
- `build`: Analyzes your codebase to extract CALLS and IMPORTS edges with advanced filtering
- `stats`: Displays node and edge statistics
- `export`: Exports to Graphviz DOT format for external visualization
- `view`: Opens interactive D3-force based viewer in browser

### Test Suggestions

```bash
# Generate test suggestions for a file or function
aston test-suggest <file_or_node> [--k 5] [--llm] [--model gpt-4o]

# Generate rich context for developers or AI agents
aston test-suggest <file_or_node> --prompt [--json context.json]

# Output in multiple formats
aston test-suggest core/auth.py --yaml tests.yaml --json tests.json

# Use LLM with budget control
aston test-suggest api/endpoints.py --llm --budget 0.01 --model gpt-4o

# Debug path resolution issues
aston test-suggest <file_or_node> --debug

# Prioritize tests based on criticality scores
aston test-suggest complex/algorithm.py --k 3 --criticality-ranked
```

**Intelligent Test Generation:**
- **Heuristic Mode**: Lightning-fast pytest skeleton generation (≤1.2s)
- **Boundary Value Testing**: Automatic edge cases for int/float, string, list, dict, bool types
- **Happy Path Coverage**: Valid input test cases for comprehensive coverage
- **Error Condition Testing**: Invalid input handling and exception testing

**LLM Integration (Optional):**
- **Fallback Strategy**: Uses LLM when heuristics can't generate suggestions
- **Cost Control**: Built-in budget tracking and enforcement
- **Model Selection**: Support for GPT-4o, GPT-4-turbo, GPT-3.5-turbo
- **Performance Guarantee**: ≤6s latency for LLM-generated suggestions

**Rich Context Mode:**
- **Developer Guidance**: Comprehensive test implementation guides
- **Parameter Analysis**: Detailed function signature and dependency analysis
- **Best Practices**: pytest patterns and testing recommendations
- **AI-Agent Ready**: Structured context for automated test generation

Options:
- `--k`: Number of suggestions to generate (default: 5)
- `--llm`: Use LLM fallback if heuristics fail (requires OPENAI_API_KEY)
- `--model`: LLM model to use (default: gpt-4o)
- `--budget`: Maximum cost per suggestion in dollars (default: $0.03)
- `--prompt`, `-p`: Generate rich context for manual test development
- `--debug`: Enable detailed debugging output for path resolution
- `--json`/`--yaml`: Output results in structured format for automation
- `--no-env-check`: Skip environment dependency check

**Examples:**
```bash
# Quick heuristic suggestions
aston test-suggest src/calculator.py --k 3

# Rich context for manual test writing
aston test-suggest user/models.py --prompt --yaml context.yaml

# LLM-powered suggestions with cost control
aston test-suggest complex/algorithm.py --llm --budget 0.005

# Target specific function
aston test-suggest "auth/login.py::authenticate_user" --debug
```

### Regression Guard

```bash
# Analyze changes for regression risk and get recommendations
aston regression-guard --since HEAD~1 [--until HEAD] [--summary-only]

# Use custom thresholds for development mode
aston regression-guard --since main \
  --max-risk-score 0.8 \
  --max-impacted-nodes 100 \
  --min-test-coverage 0.6 \
  --max-critical-nodes 15

# Generate detailed analysis for CI/CD integration
aston regression-guard --since HEAD~1 \
  --json regression-analysis.json \
  --detailed-output detailed-report.json \
  --exit-code

# Quick summary for development workflow
aston regression-guard --since HEAD~1 --summary-only --quiet

# Disable criticality-based risk assessment for comparison
aston regression-guard --since HEAD~1 --disable-criticality
```

**Intelligent Risk Assessment:**
- **Multi-Factor Scoring**: Combines node count, critical nodes, and test coverage into unified risk score
- **Threshold-Based Blocking**: Configurable limits prevent high-risk merges automatically
- **Test Execution Planning**: Prioritized test recommendations based on impact connectivity
- **Development vs Production**: Flexible thresholds for different workflow contexts
- **Criticality-Based Analysis**: Enhanced risk assessment based on node importance in the codebase

**Regression Detection:**
- **Change Impact Analysis**: Deep call graph traversal to find all affected components
- **Critical Node Detection**: Identifies high-connectivity components at risk
- **Coverage Gap Analysis**: Highlights untested code paths in changed areas
- **Risk Trend Analysis**: Tracks risk patterns across commits and branches

**CI/CD Integration:**
- **Automated Blocking**: Exit codes for CI pipeline integration
- **Rich Reporting**: JSON output for dashboard integration and automation
- **Workflow Generation**: GitHub Actions and Jenkins pipeline templates
- **Configuration Management**: YAML/JSON config files for team standards

Options:
- `--since`: Git reference to analyze changes from (required)
- `--until`: Git reference to analyze changes to (default: HEAD)
- `--max-risk-score`: Maximum allowed risk score 0.0-1.0 (default: 0.7)
- `--max-impacted-nodes`: Maximum allowed impacted nodes (default: 50)
- `--min-test-coverage`: Minimum required test coverage ratio (default: 0.8)
- `--max-critical-nodes`: Maximum allowed critical nodes (default: 10)
- `--depth`: Call graph traversal depth (default: 2)
- `--json`: Path to write detailed JSON analysis
- `--detailed-output`: Path to write comprehensive analysis with node details
- `--exit-code`: Exit with non-zero code if change should be blocked
- `--summary-only`: Show only summary table, skip detailed output

**Risk Thresholds:**
- **Production Mode**: Use default strict thresholds for release branches
- **Development Mode**: Relax thresholds for active feature development
- **Custom Contexts**: Team-specific thresholds based on codebase maturity

**Examples:**
```bash
# Standard regression check for PR
aston regression-guard --since main --summary-only

# Development-friendly thresholds
aston regression-guard --since HEAD~1 \
  --max-risk-score 0.9 \
  --max-impacted-nodes 200 \
  --min-test-coverage 0.1

# CI integration with blocking
aston regression-guard --since $BASE_BRANCH \
  --json ci-analysis.json \
  --exit-code

# Detailed analysis for complex changes
aston regression-guard --since feature-branch \
  --detailed-output full-impact.json \
  --depth 3
```

### Environment Check

```bash
# Check if all required dependencies are installed
aston check
```

Options:
- `--no-env-check`: Skip environment dependency check (also works with any command)

### Criticality Analysis

```bash
# Analyze code criticality and see top critical components
aston criticality analyze [--top 10] [--min-score 0.5]

# Export criticality scores to JSON for external tools
aston criticality export [--output criticality.json]

# Generate tuned weight configurations based on repository characteristics
aston criticality tune [--output custom_weights.yaml]
```

**Advanced Criticality Metrics:**
- **Degree Centrality**: Measures how connected a component is in the call graph
- **Call Depth Analysis**: Evaluates the depth of component in the call chain
- **Configurable Weights**: Customizable importance of different metrics through configuration
- **Drift Detection**: Identifies changes in component criticality over time
- **Impact Assessment**: Reveals which components would cause the most damage if broken

**Configuration Options:**
- `--top`: Number of critical nodes to display (default: 10)
- `--min-score`: Minimum criticality score threshold (default: 0.3)
- `--output`: Path for exporting results in JSON format
- `--config`: Path to custom weights configuration file
- `--detailed`: Show additional metrics and explanations

**Examples:**
```bash
# View top 20 most critical components
aston criticality analyze --top 20

# Export criticality data for CI/CD integration
aston criticality export --output criticality.json

# Generate custom weights based on repository structure
aston criticality tune --output custom_weights.yaml

# Use custom configuration with regression guard
aston regression-guard --since main --config custom_weights.yaml
```

### High-Performance Criticality (AstonRank)

```bash
# Use the high-performance Go-based criticality scorer (99x faster)
aston criticality analyze --engine astonrank

# Configure algorithms via YAML
aston-rank -config production.yaml -algorithm composite django-graph.json

# Generate sample configuration
aston-rank -generate-config
```

**AstonRank v2.0 Features (Week 3)**:
- **5 Algorithms**: Degree, PageRank, Composite, Betweenness, Eigenvector centrality
- **YAML Configuration**: Complex algorithm configuration with validation
- **Parallel Processing**: Multi-threaded algorithms with configurable worker pools
- **Sub-Second Performance**: 341ms total time for Django dataset (41K nodes, 43K edges)
- **Production Ready**: Comprehensive error handling, sampling optimization, profiling

**Performance Benchmarks**:
| Algorithm | Time | Memory | Scalability | Parallel |
|-----------|------|--------|-------------|----------|
| Degree | 5ms | 32MB | ✅ Excellent | ✗ |
| PageRank | 14ms | 64MB | ✅ Very Good | ✅ |
| Composite | 18ms | 68MB | ✅ Very Good | ✅ |
| Betweenness (sampled) | 150ms | 128MB | ⚠️ Good | ✅ |
| Eigenvector | 25ms | 48MB | ✅ Very Good | ✗ |

**Examples:**
```bash
# List available algorithms with parameters
aston-rank -list

# Run with configuration file
aston-rank -config configs/production.yaml -algorithm betweenness data.json

# Quick analysis with defaults
aston-rank -algorithm composite -top-k 10 django-graph.json
```

### Local Embedding Generation

```bash
# Generate embeddings for all repository files using MiniLM
aston embed --backend minilm

# Generate embeddings for specific files
aston embed --backend minilm --file src/core/*.py

# Preview what would be processed without generating embeddings
aston embed --backend minilm --dry-run

# Force regeneration of existing embeddings
aston embed --backend minilm --force

# Use specific model variant
aston embed --backend minilm --model all-MiniLM-L12-v2
```

**Local Embedding Features:**
- **MiniLM Integration**: Uses sentence-transformers for high-quality local embeddings
- **FAISS Vector Store**: High-performance similarity search with cosine distance
- **Repository-Centric**: Stores embeddings in `.aston/vectors/<backend>/index.faiss`
- **Batch Processing**: Efficient processing of large codebases with progress tracking
- **Filter Integration**: Uses unified filter system for intelligent file selection
- **No API Dependencies**: Completely local processing without external service calls

**Options:**
- `--backend`: Embedding provider to use (currently supports: `minilm`)
- `--file`: Specific file patterns to process (supports glob patterns)
- `--model`: Model variant to use (default: `all-MiniLM-L6-v2`)
- `--force`: Regenerate embeddings even if they already exist
- `--dry-run`: Preview file selection without processing

**Examples:**
```bash
# Process entire repository with MiniLM (local)
aston embed --backend minilm

# Process with OpenAI (remote)
aston embed --backend openai

# Auto-select backend (try MiniLM, fallback to OpenAI)
aston embed --backend auto

# Target specific directories
aston embed --backend minilm --file "src/**/*.py" --file "lib/**/*.py"

# OpenAI with custom settings
aston embed --backend openai --model text-embedding-3-large --rate-limit-requests 100

# Quick preview
aston embed --backend minilm --dry-run

# Use larger model for better quality
aston embed --backend minilm --model all-MiniLM-L12-v2
```

### Cache Management

```bash
# View cache statistics and performance metrics
aston cache status

# Pre-populate cache for faster operations
aston cache warm-up [--force]

# Clear cache data
aston cache clear [--confirm]
```

**Performance Acceleration:**
- **Sub-300ms Operations**: Ensures all graph operations complete in under 300ms
- **Memory Efficient**: Optimized 256MB memory limit
- **Smart Statistics**: Detailed metrics with hit ratios and latency tracking
- **Command Integration**: Seamless performance enhancement for all analysis commands

**Options:**
- `--force`: Force complete cache rebuild during warm-up
- `--confirm`: Skip confirmation prompt when clearing cache
- `--metrics-only`: Display only performance metrics in status output
- `--verbose`: Show detailed cache contents and memory usage

**Examples:**
```bash
# Check cache performance before critical operations
aston cache status --metrics-only

# Force cache rebuild after major changes
aston cache warm-up --force

# Quick cache reset
aston cache clear --confirm
```

## Use Cases

### Regression Prevention
Aston's regression guard provides automated protection against code changes that could introduce bugs:

- **Pre-Merge Validation**: Automatically assess risk before merging pull requests
- **Development Workflow**: Use relaxed thresholds during active development, strict thresholds for releases
- **CI/CD Integration**: Block high-risk merges automatically with configurable exit codes
- **Test Prioritization**: Get prioritized test execution plans based on change impact
- **Risk Visualization**: Understand change scope with detailed impact analysis and recommendations

**Example Workflow:**
```bash
# Development phase - relaxed thresholds
aston regression-guard --since main \
  --max-risk-score 0.9 \
  --max-impacted-nodes 200 \
  --min-test-coverage 0.1 \
  --summary-only

# Pre-merge validation - strict thresholds (defaults)
aston regression-guard --since main --exit-code

# CI integration with detailed reporting
aston regression-guard --since $BASE_BRANCH \
  --json ci-report.json \
  --exit-code
```

### Test Coverage Analysis
Find and prioritize testing gaps in your codebase:

- **Coverage Gap Detection**: Identify untested code paths
- **Critical Path Analysis**: Focus testing on high-impact components
- **Test Suggestions**: Generate test skeletons with boundary value analysis
- **LLM-Powered Suggestions**: Advanced test generation for complex scenarios

### Code Intelligence
Understand your codebase structure and dependencies:

- **Knowledge Graph**: Visualize call relationships and imports
- **Impact Analysis**: Understand change ripple effects
- **Repository Analysis**: Get comprehensive statistics and insights
- **Performance Cache**: Sub-300ms graph operations with minimal memory footprint

## Repository-Centric Design

Aston follows a repository-centric approach:
- All operations are relative to the repository root (current directory)
- Data is stored in `.testindex` directory at the repository root
- Path resolution is normalized for consistent matching
- Works with both offline and Neo4j storage

## Environment Variables

```
DEBUG=1                      # Enable debug logging
NEO4J_URI=bolt://localhost:7687  # Optional Neo4j connection (requires astonai[db])
NEO4J_USER=neo4j            # Optional Neo4j username (requires astonai[db])
NEO4J_PASS=password         # Optional Neo4j password (requires astonai[db])
ASTON_NO_ENV_CHECK=1        # Skip environment dependency check
OPENAI_API_KEY=sk-...       # Required for --llm features (requires astonai[llm])
```

**Package Installation Patterns:**
- **Offline Development**: `pip install astonai` → Use `aston init --offline` for fast setup
- **Live Graph Storage**: `pip install "astonai[db]"` → Use `aston init` with Neo4j 
- **Full Features**: `pip install "astonai[all]"` → All capabilities enabled

