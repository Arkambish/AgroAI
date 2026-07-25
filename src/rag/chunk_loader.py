"""Load and format knowledge chunks for the AgriSense RAG corpus."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLACEHOLDER_DIR = os.path.join(ROOT, 'data', 'rag', 'placeholder')


@dataclass
class Chunk:
    id: str
    text: str
    source_type: str
    district: str = ''
    season: str = ''
    source_file: str = ''


def _format_prediction_chunk(data: dict[str, Any], source_file: str) -> Chunk:
    district = data.get('district', '')
    season = data.get('season', '')
    text = (
        f"Yield prediction for {district} {season} {data.get('year', '')}: "
        f"predicted {data.get('predicted_yield_MT_per_Ha')} MT/Ha "
        f"(95% CI: {data.get('confidence_lower')}–{data.get('confidence_upper')} MT/Ha). "
        f"Model: {data.get('model')} (R²={data.get('model_r2')}). "
        f"Confidence label: {data.get('confidence')}. "
        f"{data.get('notes', '')}"
    )
    return Chunk(
        id=f"prediction_{district.lower()}_{season.lower()}",
        text=text.strip(),
        source_type='PREDICTION',
        district=district,
        season=season,
        source_file=source_file,
    )


def _format_shap_chunk(data: dict[str, Any], source_file: str) -> Chunk:
    district = data.get('district', '')
    season = data.get('season', '')
    features = data.get('top_features', [])
    feature_lines = ', '.join(
        f"{f['name']} (mean |SHAP|={f['mean_abs_shap']})" for f in features
    )
    text = (
        f"SHAP feature attribution for {district} {season}. "
        f"Top drivers: {feature_lines}. "
        f"{data.get('interpretation', '')}"
    )
    return Chunk(
        id=f"shap_{district.lower()}_{season.lower()}",
        text=text.strip(),
        source_type='SHAP',
        district=district,
        season=season,
        source_file=source_file,
    )


def _format_uncertainty_chunk(data: dict[str, Any], source_file: str) -> Chunk:
    example = data.get('example', {})
    district = example.get('district', '')
    season = example.get('season', '')
    text = (
        f"LOYO-CV uncertainty for AgriSense model ({data.get('model')}): "
        f"RMSE={data.get('rmse')} MT/Ha, MAE={data.get('mae')} MT/Ha, "
        f"R²={data.get('r2')}, MAPE={data.get('mape')}%. "
        f"Method: {data.get('confidence_interval_method')}. "
        f"Example for {district} {season}: predicted "
        f"{example.get('predicted_yield_MT_per_Ha')} MT/Ha, "
        f"interval {example.get('confidence_lower')}–{example.get('confidence_upper')} MT/Ha. "
        f"{data.get('notes', '')}"
    )
    return Chunk(
        id=f"uncertainty_{district.lower()}_{season.lower()}",
        text=text.strip(),
        source_type='UNCERTAINTY',
        district=district,
        season=season,
        source_file=source_file,
    )


def _format_oof_chunk(data: dict[str, Any], source_file: str) -> Chunk:
    district = data.get('district', '')
    season = data.get('season', '')
    text = (
        f"LOYO-CV out-of-fold result ({data.get('model_name')}) for "
        f"{district} {season} {data.get('year')}: "
        f"actual {data.get('actual_yield_MT_per_Ha')} MT/Ha, "
        f"predicted {data.get('predicted_yield_MT_per_Ha')} MT/Ha, "
        f"error {data.get('prediction_error_MT_per_Ha')} MT/Ha. "
        f"{data.get('notes', '')}"
    )
    return Chunk(
        id=f"oof_{district.lower()}_{season.lower()}_{data.get('year')}",
        text=text.strip(),
        source_type='UNCERTAINTY',
        district=district,
        season=season,
        source_file=source_file,
    )


def _format_cultivation_chunk(text: str, source_file: str) -> Chunk:
    return Chunk(
        id='cultivation_onion_sri_lanka',
        text=text.strip(),
        source_type='CULTIVATION',
        source_file=source_file,
    )


class ChunkLoader(ABC):
    @abstractmethod
    def load(self) -> list[Chunk]:
        ...


class PlaceholderChunkLoader(ChunkLoader):
    """Load the small placeholder corpus from data/rag/placeholder/."""

    def __init__(self, corpus_dir: str | None = None) -> None:
        self.corpus_dir = corpus_dir or PLACEHOLDER_DIR

    def load(self) -> list[Chunk]:
        chunks: list[Chunk] = []
        formatters: dict[str, tuple[Any, str]] = {
            'prediction_matale_yala.json': (_format_prediction_chunk, 'PREDICTION'),
            'shap_features.json': (_format_shap_chunk, 'SHAP'),
            'uncertainty_metrics.json': (_format_uncertainty_chunk, 'UNCERTAINTY'),
            'oof_matale_yala.json': (_format_oof_chunk, 'UNCERTAINTY'),
        }

        for filename, (formatter, _) in formatters.items():
            path = os.path.join(self.corpus_dir, filename)
            if not os.path.exists(path):
                continue
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            rel = f'placeholder/{filename}'
            chunks.append(formatter(data, rel))

        cultivation_path = os.path.join(self.corpus_dir, 'onion_cultivation.txt')
        if os.path.exists(cultivation_path):
            with open(cultivation_path, encoding='utf-8') as f:
                chunks.append(
                    _format_cultivation_chunk(f.read(), 'placeholder/onion_cultivation.txt')
                )

        return chunks


class AgriSenseChunkLoader(ChunkLoader):
    """Future loader: build chunks from live AgriSense pipeline outputs."""

    def __init__(self, results_dir: str) -> None:
        self.results_dir = results_dir

    def load(self) -> list[Chunk]:
        chunks: list[Chunk] = []

        fi_path = os.path.join(self.results_dir, 'feature_importance.json')
        if os.path.exists(fi_path):
            with open(fi_path, encoding='utf-8') as f:
                features = json.load(f)
            shap_data = {
                'district': '',
                'season': '',
                'top_features': features[:5],
                'interpretation': (
                    'Global SHAP feature importance from the best AgriSense model.'
                ),
            }
            chunks.append(
                _format_shap_chunk(shap_data, 'results/feature_importance.json')
            )

        metrics_path = os.path.join(self.results_dir, 'best_model_metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path, encoding='utf-8') as f:
                metrics = json.load(f)
            uncertainty_data = {
                'model': metrics.get('Model', metrics.get('model', 'unknown')),
                'rmse': metrics.get('RMSE', metrics.get('rmse')),
                'mae': metrics.get('MAE', metrics.get('mae')),
                'r2': metrics.get('R2', metrics.get('r2')),
                'mape': metrics.get('MAPE', metrics.get('mape')),
                'confidence_interval_method': '95% CI using LOYO-CV RMSE: margin = 1.96 × RMSE',
                'example': {},
                'notes': 'Derived from best_model_metrics.json in the AgriSense pipeline.',
            }
            chunks.append(
                _format_uncertainty_chunk(
                    uncertainty_data, 'results/best_model_metrics.json'
                )
            )

        return chunks


def get_chunk_loader(corpus: str = 'placeholder', results_dir: str = '') -> ChunkLoader:
    if corpus == 'agrisense':
        if not results_dir:
            raise ValueError('results_dir is required when RAG_CORPUS=agrisense')
        return AgriSenseChunkLoader(results_dir)
    return PlaceholderChunkLoader()
