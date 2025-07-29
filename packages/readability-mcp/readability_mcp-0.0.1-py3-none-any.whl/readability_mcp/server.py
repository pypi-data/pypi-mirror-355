#!/usr/bin/env python3

import textstat
from textblob import TextBlob
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel


class TextStats(BaseModel):
    sentence_count: int
    word_count: int
    character_count: int
    syllable_count: int


class SentimentAnalysis(BaseModel):
    polarity: float  # -1 (negative) to 1 (positive)
    subjectivity: float  # 0 (objective) to 1 (subjective)
    interpretation: str


class Interpretation(BaseModel):
    flesch_ease_interpretation: str
    overall_difficulty: str
    recommendations: list[str]


class ReadabilityResults(BaseModel):
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float
    smog_index: float
    automated_readability_index: float
    coleman_liau_index: float
    reading_time_seconds: float
    text_stats: TextStats
    sentiment: SentimentAnalysis
    interpretation: Interpretation


mcp = FastMCP("readability-server")


@mcp.tool()
def analyze_readability(text: str) -> str:
    """Analyze text readability using multiple metrics"""
    if not text.strip():
        return "Error: Empty text provided"

    try:
        text_stats = TextStats(
            sentence_count=textstat.sentence_count(text),
            word_count=textstat.lexicon_count(text, removepunct=True),
            character_count=textstat.char_count(text, ignore_spaces=True),
            syllable_count=textstat.syllable_count(text),
        )

        flesch_ease = textstat.flesch_reading_ease(text)
        fk_grade = textstat.flesch_kincaid_grade(text)
        gunning_fog = textstat.gunning_fog(text)

        blob = TextBlob(text)
        sentiment = SentimentAnalysis(
            polarity=blob.sentiment.polarity,
            subjectivity=blob.sentiment.subjectivity,
            interpretation=_interpret_sentiment(
                blob.sentiment.polarity, blob.sentiment.subjectivity
            ),
        )

        interpretation = Interpretation(
            flesch_ease_interpretation=_interpret_flesch_ease(flesch_ease),
            overall_difficulty=_get_overall_difficulty(fk_grade),
            recommendations=_get_recommendations(flesch_ease, gunning_fog, text_stats),
        )

        results = ReadabilityResults(
            flesch_reading_ease=flesch_ease,
            flesch_kincaid_grade=fk_grade,
            gunning_fog=gunning_fog,
            smog_index=textstat.smog_index(text),
            automated_readability_index=textstat.automated_readability_index(text),
            coleman_liau_index=textstat.coleman_liau_index(text),
            reading_time_seconds=textstat.reading_time(text, ms_per_char=14.69),
            text_stats=text_stats,
            sentiment=sentiment,
            interpretation=interpretation,
        )

        return results.model_dump_json(indent=2)

    except Exception as e:
        return f"Error analyzing text: {str(e)}"


@mcp.tool()
def flesch_reading_ease(text: str) -> str:
    """Get Flesch Reading Ease score (0-100, higher = easier)"""
    if not text.strip():
        return "Error: Empty text provided"

    try:
        score = textstat.flesch_reading_ease(text)
        interpretation = _interpret_flesch_ease(score)
        return f"Flesch Reading Ease: {score:.1f}\nInterpretation: {interpretation}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def flesch_kincaid_grade(text: str) -> str:
    """Get Flesch-Kincaid Grade Level"""
    if not text.strip():
        return "Error: Empty text provided"

    try:
        grade = textstat.flesch_kincaid_grade(text)
        return f"Flesch-Kincaid Grade Level: {grade:.1f}\nInterpretation: Readable by someone with {grade:.1f} years of education"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def analyze_sentiment(text: str) -> str:
    """Analyze text sentiment and subjectivity"""
    if not text.strip():
        return "Error: Empty text provided"

    try:
        blob = TextBlob(text)
        sentiment = SentimentAnalysis(
            polarity=blob.sentiment.polarity,
            subjectivity=blob.sentiment.subjectivity,
            interpretation=_interpret_sentiment(
                blob.sentiment.polarity, blob.sentiment.subjectivity
            ),
        )
        return sentiment.model_dump_json(indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


def _interpret_sentiment(polarity: float, subjectivity: float) -> str:
    polarity_desc = next(
        desc
        for threshold, desc in [
            (0.1, "Positive"),
            (-0.1, "Neutral"),
            (-1.0, "Negative"),
        ]
        if polarity >= threshold
    )

    subjectivity_desc = next(
        desc
        for threshold, desc in [
            (0.6, "Highly subjective"),
            (0.3, "Moderately subjective"),
            (0.0, "Objective"),
        ]
        if subjectivity >= threshold
    )

    return f"{polarity_desc} tone, {subjectivity_desc.lower()}"


def _interpret_flesch_ease(score: float) -> str:
    thresholds = [
        (90, "Very Easy (5th grade level)"),
        (80, "Easy (6th grade level)"),
        (70, "Fairly Easy (7th grade level)"),
        (60, "Standard (8th-9th grade level)"),
        (50, "Fairly Difficult (10th-12th grade level)"),
        (30, "Difficult (college level)"),
        (0, "Very Difficult (graduate level)"),
    ]
    return next(desc for threshold, desc in thresholds if score >= threshold)


def _get_overall_difficulty(fk_grade: float) -> str:
    thresholds = [
        (16, "Graduate"),
        (12, "College"),
        (9, "High School"),
        (6, "Middle School"),
        (0, "Elementary"),
    ]
    return next(desc for threshold, desc in thresholds if fk_grade > threshold)


def _get_recommendations(
    flesch_ease: float, gunning_fog: float, text_stats: TextStats
) -> list[str]:
    avg_sentence_length = text_stats.word_count / max(text_stats.sentence_count, 1)

    recommendations = [
        rec
        for condition, rec in [
            (flesch_ease < 60, "Consider using shorter sentences"),
            (flesch_ease < 60, "Replace complex words with simpler alternatives"),
            (
                avg_sentence_length > 20,
                f"Break up long sentences (current average: {avg_sentence_length:.1f} words per sentence)",
            ),
            (gunning_fog > 12, "Reduce use of complex words and jargon"),
        ]
        if condition
    ]

    return recommendations or ["Text readability is good!"]


def main():
    mcp.run()


if __name__ == "__main__":
    main()
