# Readability Analysis MCP Server

A Model Context Protocol (MCP) server that provides comprehensive text readability analysis using multiple established metrics. Built with FastMCP and Pydantic for reliable, structured analysis.

## Features

- **Multiple Readability Metrics**: Flesch Reading Ease, Flesch-Kincaid Grade Level, Gunning Fog Index, SMOG Index, ARI, and Coleman-Liau Index
- **Text Statistics**: Word count, sentence count, character count, syllable count, and estimated reading time
- **Sentiment Analysis**: Polarity and subjectivity analysis using TextBlob
- **Intelligent Interpretations**: Human-readable explanations and improvement recommendations
- **Structured Output**: JSON responses with Pydantic models for reliable parsing

## All Platforms Configuration

Edit your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "readability": {
      "command": "uvx",
      "args": ["readability-mcp"]
    }
  }
}
```

## Usage Examples

Once configured, restart Claude Desktop and you can use the readability tools directly in conversation:

### Quick Readability Check

```text
Can you analyze the readability of this text:
"The implementation of advanced algorithmic methodologies necessitates comprehensive evaluation protocols to ensure optimal performance characteristics across diverse operational parameters."
```

Claude will use your `analyze_readability` tool and provide structured analysis.

### Sentiment Analysis

```text
What's the sentiment of this customer feedback:
"I absolutely love this product! It's incredibly easy to use and has made my workflow so much more efficient."
```

Claude will use your `analyze_sentiment` tool.

### Specific Metrics

```text
What's the Flesch Reading Ease score for my blog post draft?
[paste your content]
```

Claude will use your `flesch_reading_ease` tool.

## Integration Benefits

1. **Seamless Experience**: Tools appear as native Claude capabilities
2. **Structured Analysis**: Pydantic models ensure consistent, parseable responses
3. **Multi-tool Workflow**: Claude can chain multiple readability tools together
4. **Context Aware**: Claude can provide writing suggestions based on your analysis

## Example Workflow

**You**: "Help me improve this paragraph for a general audience"

**Claude**: First, let me analyze the current readability...
*[Uses analyze_readability tool]*

Based on the analysis showing a Flesch-Kincaid grade level of 14.2 (college level), here are some suggestions to make it more accessible:

1. Break up the 45-word sentence into 2-3 shorter ones
2. Replace "methodologies" with "methods"
3. Simplify "necessitates" to "requires"

**You**: "Can you rewrite it and check the new version?"

**Claude**: *[Rewrites the text, then uses analyze_readability again to verify improvement]*

## Usage

### Available Tools

#### `analyze_readability(text: str)`

Comprehensive analysis including all metrics, statistics, sentiment, and recommendations.

**Example:**

```json
{
  "flesch_reading_ease": 65.2,
  "flesch_kincaid_grade": 8.1,
  "gunning_fog": 10.3,
  "smog_index": 9.8,
  "automated_readability_index": 8.7,
  "coleman_liau_index": 9.2,
  "reading_time_seconds": 45.6,
  "text_stats": {
    "sentence_count": 5,
    "word_count": 87,
    "character_count": 456,
    "syllable_count": 132
  },
  "sentiment": {
    "polarity": 0.2,
    "subjectivity": 0.4,
    "interpretation": "Positive tone, moderately subjective"
  },
  "interpretation": {
    "flesch_ease_interpretation": "Standard (8th-9th grade level)",
    "overall_difficulty": "High School",
    "recommendations": ["Text readability is good!"]
  }
}
```

#### `flesch_reading_ease(text: str)`

Returns only the Flesch Reading Ease score with interpretation.

#### `flesch_kincaid_grade(text: str)`

Returns only the Flesch-Kincaid Grade Level.

#### `analyze_sentiment(text: str)`

Returns sentiment analysis with polarity, subjectivity, and interpretation.

## Readability Metrics Explained

| Metric | Range | Description |
|--------|-------|-------------|
| **Flesch Reading Ease** | 0-100 | Higher scores = easier to read |
| **Flesch-Kincaid Grade** | 0-18+ | Grade level required to understand |
| **Gunning Fog Index** | 6-17+ | Years of education needed |
| **SMOG Index** | 6-18+ | Simple Measure of Gobbledygook |
| **ARI** | 1-14+ | Automated Readability Index |
| **Coleman-Liau** | 1-16+ | Based on characters per word |

### Reading Ease Interpretations

- **90-100**: Very Easy (5th grade)
- **80-89**: Easy (6th grade)
- **70-79**: Fairly Easy (7th grade)
- **60-69**: Standard (8th-9th grade)
- **50-59**: Fairly Difficult (10th-12th grade)
- **30-49**: Difficult (college level)
- **0-29**: Very Difficult (graduate level)

## License

MIT
