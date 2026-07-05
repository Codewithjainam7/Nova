# NOVA Vision Engine Architecture

## 1. Overview
The NOVA Vision Engine is the exclusive centralized subsystem for all image-based processing. It handles raw screenshots from the Desktop or Browser engines and runs them through a pipeline of preprocessing, OCR (Optical Character Recognition), and Object Detection to generate structured bounding box data for the AI runtime.

## 2. Responsibilities
- **Image Preprocessing:** Safely crops, resizes, and normalizes raw byte streams (e.g. contrast enhancement for better OCR yield).
- **OCR Orchestration:** Extracts text and maps its absolute coordinates using engines like Tesseract or Windows native OCR.
- **UI & Object Detection:** Detects non-text semantic elements (buttons, inputs, dropdowns) using specialized ML models (e.g. YOLO/ONNX).
- **Region Management:** Constructs interactive bounding boxes, translating visual screen real estate into programmatic interaction targets for the Desktop/Browser engines.
- **Permissions:** Enforces boundaries (e.g., preventing OCR on regions marked as sensitive, like password managers).

## 3. Internal Components
- **VisionEngine (Core):** Public API and orchestrator.
- **VisionManager:** Injects dependencies and configurations.
- **VisionExecutor:** Lifecycle management (Auth -> Pipeline -> Cache/Metrics -> Return).
- **VisionPipeline:** The deterministic sequence: Preprocess -> OCR -> UI Detect -> Merge.
- **VisionPermissionManager:** Validates visual read boundaries.
- **VisionRecoveryManager:** Provides fallback models if the primary OCR engine crashes.
- **VisionCache:** Stores hashed analysis results of static screen regions to save compute latency.
- **Adapters:**
  - `ImagePreprocessor`, `ImageNormalizer`, `ImageResizer`, `ImageCropper`, `ImageAnnotator`, `ColorAnalyzer`.
  - `ScreenAnalyzer`, `OCRManager`, `UIAnalyzer`, `ObjectDetector`, `RegionSelector`, `TextExtractor`, `LayoutAnalyzer`.

## 4. Folder Structure
```text
backend/vision/
├── schema.py        # VisionSession, VisionBoundingBox, VisionResult, Metrics
├── processing.py    # Resizer, Cropper, Normalizer, Annotator
├── analysis.py      # OCR, UI Analyzer, Object Detector
├── core.py          # Engine, Executor, Manager, Pipeline, Cache
```

## 5. Mermaid Class Diagram
```mermaid
classDiagram
    class VisionEngine {
        +analyze_screen(image_data)
        +extract_text(image_data)
    }
    class VisionExecutor {
        +execute_full_screen()
    }
    class VisionPipeline {
        +run_pipeline()
    }
    class ScreenAnalyzer {
        +analyze_screen()
    }
    class OCRManager {
        +extract()
    }
    class UIAnalyzer {
        +analyze_ui()
    }
    class ImagePreprocessor {
        +process_for_ocr()
    }

    VisionEngine --> VisionExecutor
    VisionExecutor --> VisionPipeline
    VisionPipeline --> ImagePreprocessor
    VisionPipeline --> ScreenAnalyzer
    ScreenAnalyzer --> OCRManager
    ScreenAnalyzer --> UIAnalyzer
```

## 6. Mermaid Flow Diagram
```mermaid
flowchart TD
    A[Execution Engine] --> B[VisionEngine: analyze_screen]
    B --> C[VisionExecutor]
    C --> D{Permission Check}
    D -- Denied --> E[Raise PermissionError]
    D -- Allowed --> F{Cache Hit?}
    F -- Yes --> G[Return Cached Result]
    F -- No --> H[VisionPipeline]
    H --> I[ImagePreprocessor]
    I --> J[ScreenAnalyzer]
    J --> K[OCR Extraction]
    J --> L[UI Object Detection]
    K --> M[Merge Bounding Boxes]
    L --> M
    M --> N[Update Metrics & Cache]
    N --> O[Return VisionResult]
```

## 7. Mermaid Sequence Diagram
```mermaid
sequenceDiagram
    participant EE as Execution Engine
    participant VE as Vision Engine
    participant Pipe as Pipeline
    participant Prep as Preprocessor
    participant OCR
    participant UI as UI Analyzer

    EE->>VE: analyze_screen(screenshot_bytes)
    VE->>Pipe: run_pipeline(screenshot_bytes)
    
    Pipe->>Prep: process_for_ocr()
    Prep-->>Pipe: normalized_bytes
    
    Pipe->>OCR: extract(normalized_bytes)
    OCR-->>Pipe: text_boxes
    
    Pipe->>UI: analyze_ui(normalized_bytes)
    UI-->>Pipe: object_boxes
    
    Pipe->>Pipe: Merge(text_boxes, object_boxes)
    Pipe-->>VE: VisionResult
    VE-->>EE: VisionResult
```

## 8. Mermaid State Diagram
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Validating : Image Received
    Validating --> Preprocessing : Authorized
    Validating --> Rejected : Unauthorized
    Preprocessing --> Analysis
    
    state Analysis {
        [*] --> ExtractingOCR
        [*] --> DetectingObjects
        ExtractingOCR --> Merging
        DetectingObjects --> Merging
    }
    
    Analysis --> Success
    Analysis --> Failed : Model Exception
    Failed --> Recovering
    Recovering --> Analysis : Fallback Model
    Recovering --> FatalError
    Success --> Caching
    Caching --> Idle
    FatalError --> Idle
```

## 9. Dependency Graph
- Depends on: Pydantic, Pillow, Tesseract/ONNX (future).
- Consumed by: Execution Engine, Verification Engine, Memory Engine (Contextual snapshots).

## 10. Public API
- `VisionEngine.analyze_screen(image_data: bytes) -> VisionResult`
- `VisionEngine.extract_text(image_data: bytes) -> VisionResult`

## 11. Vision Pipeline
1. Image Byte Stream received.
2. Normalized for contrast/brightness.
3. Passed to OCR Manager for textual bounding boxes.
4. Passed to YOLO/Object Detector for semantic UI bounding boxes.
5. Consolidated into a single `VisionResult` DTO.

## 12. OCR Pipeline
1. Isolate text blocks via contours.
2. Deskew and binarize.
3. Tesseract recognition.
4. Confidence threshold filtering.

## 13. Performance Considerations
- ML inference blocks the thread. Final implementation will require `asyncio.to_thread()` or a dedicated subprocess pool for YOLO/Tesseract execution.

## 14. Future Improvements
- Integrate visual grounding LLMs (e.g., LLaVa or Qwen-VL) to replace deterministic YOLO object detection with semantic reasoning.
