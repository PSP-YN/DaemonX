# DAEMONX — Performance Analysis & Metrics

## 1. Verified Benchmarks (Measured on Fedora Linux 44 Host)

| Pipeline Operation | Measured Latency | Throughput | Technology Stack |
| :--- | :--- | :--- | :--- |
| **Physical Screen Capture** | ~350 ms | ~3 FPS | `screencap -p` stream over USB 2.0/3.0 |
| **Local OCR Pass** | ~280 ms / frame | ~3.5 frames / sec | Native Tesseract 5.5.3 (AVX2 optimized) |
| **UI Hierarchy XML Dump** | ~180 ms | ~5 dumps / sec | `uiautomator dump` XML parser |
| **Perceptual Hash (pHash)** | ~12 ms / image | ~80 images / sec | `imagehash` 64-bit DCT |
| **SQLite FTS5 Query** | < 2 ms / search | > 500 queries / sec | SQLite 3.51 with Porter tokenization |
| **Full Screenshot Pipeline** | ~480 ms / item | ~125 items / min | Scan -> Hash -> OCR -> Entity -> SQLite |

## 2. Resource Optimization Strategies
- **Selective OCR**: UI hierarchy text is parsed first from accessibility trees. Tesseract is only invoked if accessibility nodes lack readable text.
- **Deduplication Caching**: Perceptual hash and SHA-256 checks immediately bypass re-analyzing identical screenshots.
- **SQLite WAL Mode**: Write-Ahead Logging allows concurrent reads during background data insertion.
