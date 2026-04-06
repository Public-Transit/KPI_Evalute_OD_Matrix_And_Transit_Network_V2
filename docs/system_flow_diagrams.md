# System Flow Diagrams (Mermaid)

Tai lieu nay mo ta luong hoat dong toan bo chuong trinh KPI Evaluation Bus, gom:

1. Flowchart tong the
2. Data Flow Diagram (DFD level 1)
3. Activity Diagram chi tiet nghiep vu

---

## 1. Flowchart Tong The

```mermaid
flowchart TD
    A[Client goi API KPI] --> B[FastAPI App]
    B --> C{Chon endpoint}

    C -->|POST /api/kpi/calculate-all| D[Khoi tao repo, uow, routing engine, filter, geo calculator]
    C -->|POST /api/kpi/calculate-all-routes| E[Khoi tao repo, uow, routing engine, geo calculator]

    D --> F[batch_route_all_od_pairs]
    F --> G[Doc du lieu: stops, routes, zones, od_pairs, trips]
    G --> H[Tao TransitNetwork va ODMatrix]
    H --> I[GenerateODRoutingResultService]
    I --> J[For moi OD pair: tim CandidateTrip]
    J --> K[Filter moi CandidateTrip thanh Representative Trip]
    K --> L[Tao EvaluatedRoutingOption]
    L --> M[Tao ODRoutingResultV2 cho tung OD]

    M --> N[For moi routing option: tinh Transfer, Circuity, Spatial Coverage]
    N --> O[Tinh Composite score]
    O --> P[ODKPIAggregator tong hop OD-level]
    P --> Q[Sort option theo composite giam dan va danh OPT1..OPTn]
    Q --> R[Tra JSON success cho OD KPI]

    E --> S[calculate_kpis_for_all_trips]
    S --> T[Doc du lieu va tao TransitNetwork/ODMatrix]
    T --> U[For moi Trip trong repo]
    U --> V[TotalPotentialDemandInTripCalculator]
    V --> W[Loop tat ca OD pair de xac dinh OD duoc trip phuc vu]
    W --> X[Tong total_demand va danh sach served_od_pairs]
    X --> Y[Build summary/path cho trip]
    Y --> Z[Sort trip theo total_potential_demand giam dan]
    Z --> AA[Tra JSON success cho Trip KPI]

    R --> AB[End]
    AA --> AB
```

### Giai thich nhanh
- He thong co 2 luong API chinh: OD-level KPI va Trip-level KPI.
- Moi luong deu bat dau tu fake repository, sau do dung domain object roi tinh KPI.
- Dau ra duoc rut gon va sort de phuc vu giao dien/API consumer.

---

## 2. Data Flow Diagram (DFD - Level 1)

```mermaid
flowchart LR
    U[External User or UI] -->|HTTP POST| P1[API Controller]

    D1[(Fake Repository Data)]
    D2[(In-memory Domain Objects)]
    D3[(OD KPI Results)]
    D4[(Trip KPI Results)]

    P1 -->|Yeu cau nap du lieu| P2[UnitOfWork + Repository]
    P2 -->|stops routes zones od_pairs trips| D1
    P2 -->|raw data| P3[Domain Object Builder]
    P3 -->|TransitNetwork ODMatrix| D2

    P1 -->|OD KPI flow| P4[Routing Service]
    D2 --> P4
    P4 -->|ODRoutingResult list| P5[OD KPI Calculators]
    D2 --> P5
    P5 -->|option-level KPI| P6[OD Aggregator]
    P6 -->|summary + route_options| D3

    P1 -->|Trip KPI flow| P7[Trip KPI Service]
    D2 --> P7
    P7 -->|trip-level KPI| D4

    D3 -->|JSON response| P1
    D4 -->|JSON response| P1
    P1 -->|HTTP JSON| U
```

### Giai thich nhanh
- P1 la entrypoint FastAPI trong src/entrypoints/api.py.
- P2-P3 la khoi tai du lieu va chuyen thanh model domain.
- P4-P6 la pipeline OD KPI.
- P7 la pipeline Trip KPI.
- D3, D4 la du lieu ket qua tra ve cho client.

---

## 3. Activity Diagram Chi Tiet

```mermaid
flowchart TD
    S((Start)) --> A[Nhap request]
    A --> B{Endpoint nao?}

    B -->|calculate-all| C[Khoi tao thanh phan OD KPI]
    C --> D[Doc data va tao TransitNetwork ODMatrix]
    D --> E[For tung OD pair]
    E --> F[Routing: tim candidate trips direct + 1 transfer]
    F --> G{Co candidate trip khong?}
    G -->|Khong| H[Tao OD result voi option rong]
    G -->|Co| I[For moi candidate trip]
    I --> J[Filter thanh representative trip toi uu]
    J --> K[Tao EvaluatedRoutingOption]
    K --> L[Tinh transfer circuity coverage]
    L --> M[Tinh composite cho option]
    M --> N[Them vao danh sach option KPI]
    N --> O{Con candidate?}
    O -->|Co| I
    O -->|Khong| P[Aggregate OD-level voi hard-threshold]
    P --> Q{Con option hop le sau loc?}
    Q -->|Khong| R[summary invalid + diem null]
    Q -->|Co| T[summary valid + diem 0-100]
    R --> U[Sort route_options + gan OPT index]
    T --> U
    U --> V{Con OD pair?}
    V -->|Co| E
    V -->|Khong| W[Tra response success cho OD KPI]

    B -->|calculate-all-routes| C2[Khoi tao thanh phan Trip KPI]
    C2 --> D2[Doc data va tao TransitNetwork ODMatrix]
    D2 --> E2[For tung trip]
    E2 --> F2[TotalPotentialDemand calculator]
    F2 --> G2[For tung OD pair: kiem tra trip co phuc vu duoc OD khong]
    G2 --> H2[Cong don demand va served_od_pairs]
    H2 --> I2[Build summary + path cho trip]
    I2 --> J2{Con trip?}
    J2 -->|Co| E2
    J2 -->|Khong| K2[Sort giam dan theo total_potential_demand]
    K2 --> L2[Tra response success cho Trip KPI]

    W --> Z((End))
    L2 --> Z
```

### Giai thich nhanh
- Nhanh OD KPI:
  - Routing tao cac candidate trip.
  - Filter chon representative trip toi uu theo khoang cach tiep can + khoang cach tren tuyen.
  - Tinh 3 KPI option-level: transfer, circuity, spatial coverage.
  - Composite calculator quy doi score ve thang 0-100.
  - Aggregator loc theo nguong va tong hop OD-level.

- Nhanh Trip KPI:
  - Duyet tung trip cua repository.
  - Kiem tra tung OD pair co duoc trip do phuc vu hay khong.
  - Cong don total potential demand va luu chi tiet served_od_pairs.
  - Sort trip theo demand giam dan de tra ket qua.

---

## 4. Formula va Rule Quan Trong

### 4.1 Composite score (option-level)

Y tuong tong quat:

- Transfer cang it cang tot
- Circuity cang gan 1 cang tot
- Coverage cang cao cang tot

Cong thuc:

- Composite = 0.45 * Transfer_norm + 0.20 * Circuity_norm + 0.35 * Coverage_norm

### 4.2 OD-level aggregate

- Loc hard-threshold:
  - transfer <= 1
  - circuity <= 2.5
  - spatial coverage >= 0.1

- Neu khong con option hop le:
  - summary.is_valid = false
  - summary.reason = No valid trips after hard-threshold filtering
  - scores = null

- Neu con option hop le:
  - OD_score = alpha * best + (1 - alpha) * weighted_average
  - alpha mac dinh = 0.7

---

## 5. Mapping sang Source Code

- API entrypoint: src/entrypoints/api.py
- OD orchestration: src/service_layer/service/routing_services.py
- Trip orchestration: src/service_layer/service/trip_kpi_services.py
- Routing generation: src/domain/service/generate_od_routing_result.py
- Routing engines: src/domain/service/routing.py
- Candidate filter: src/domain/service/filter.py
- KPI calculators:
  - src/domain/service/kpi_caculator/transfer_kpi.py
  - src/domain/service/kpi_caculator/circuity_kpi.py
  - src/domain/service/kpi_caculator/spatial_coverage_kpi.py
- Composite + aggregator:
  - src/domain/service/aggregate/composite_quality_index.py
  - src/domain/service/aggregate/od_kpi_aggregator.py
- Trip KPI calculator:
  - src/domain/service/trip_kpi_caculator/total_potential_demand_in_trip.py
- Data source fake repo: src/adapters/repository/fake_repo_grid_3x3.py

---

## 6. Ket Luan

- Chuong trinh duoc to chuc ro theo DDD + service layer.
- Luong tinh KPI tach biet theo OD-level va Trip-level.
- Diagram tren co the dua truc tiep vao docs ky thuat, bao cao nghiep vu, hoac onboarding dev moi.
