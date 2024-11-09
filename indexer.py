from flask import Flask, request, jsonify
from pathlib import Path
from pydantic import BaseModel
import numpy as np
import faiss
import pickle
from typing import Optional
from embedding import get_single_text_embedding