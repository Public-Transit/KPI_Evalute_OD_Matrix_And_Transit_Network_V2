# API KPI Response Contract

## Endpoint

- Method: `POST`
- Path: `/api/kpi/calculate-all`

Endpoint nay tra ve ket qua KPI da duoc rut gon theo tung OD pair, phu hop cho consumer nghiep vu va giao dien.

## Response Envelope

```json
{
  "status": "success",
  "data": [
    {
      "od_pair_id": "OD1",
      "summary": {
        "is_valid": true,
        "reason": null,
        "scores": {
          "composite": 46.75,
          "transfer": 66.67,
          "circuity": 40.0,
          "spatial_coverage": 25.0
        }
      },
      "route_options": [
        {
          "option_id": "OPT1",
          "path": {
            "route_sequence": ["Tuyen R1", "Tuyen R2"],
            "stop_sequence": ["Tram A", "Tram B", "Tram C"]
          },
          "metrics": {
            "composite_score": 46.75,
            "transfer_count": 1,
            "circuity_index": 1.9,
            "coverage_ratio": 0.25
          }
        }
      ]
    }
  ]
}
```

Schema mau 1 OD cung duoc luu tai [template_json.json](/e:/VTS/ITS/KPI%20Evaluation%20Bus/KPI_Evalute_OD_Matrix_And_Transit_Network_V2/src/entrypoints/template_json.json).

## Field Guide

- `status`: trang thai xu ly cua API. Hien tai tra ve `success` neu tinh toan thanh cong.
- `data`: danh sach ket qua theo OD pair.
- `od_pair_id`: ma OD pair.
- `summary.is_valid`: cho biet OD co du dieu kien de tong hop cap OD hay khong.
- `summary.reason`: ly do invalid. Bang `null` neu hop le.
- `summary.scores`: cac diem OD-level da duoc chuan hoa ve thang `0-100`.
- `route_options`: danh sach phuong an dai dien cua OD.
- `route_options[].path`: lo trinh dai dien gom chuoi tuyen va chuoi tram.
- `route_options[].metrics`: chi giu 4 metric nghiep vu cot loi o muc option.

## Ordering Rules

- `route_options` duoc sap xep theo `metrics.composite_score` giam dan.
- Option co `composite_score = null` duoc day xuong cuoi danh sach.
- `option_id` duoc danh lai sau khi sort theo thu tu `OPT1`, `OPT2`, `OPT3`, ...

## Invalid Summary Behavior

Neu tat ca option cua mot OD bi loai tai buoc aggregate:

- `summary.is_valid = false`
- `summary.reason = "No valid trips after hard-threshold filtering"`
- tat ca `summary.scores.* = null`
- `route_options` van duoc giu lai o dang rut gon de consumer van xem duoc cac phuong an da danh gia

## Removed From Public Contract

Contract moi khong con tra ve cac field debug/noi bo sau:

- `aggregated_kpis`
- `candidate_routes`
- `representative_trip`
- `kpis`
- `score_scale`
- `best_score`
- `weighted_average_score`
- `parameters`
- `invalid_inputs`
- `raw_inputs`
- `normalized_scores`
- `weights`
- `weighted_scores`
- `origin_coverage_ratio`
- `destination_coverage_ratio`
- `origin_zone_id`
- `destination_zone_id`
- `radius_m`
- `origin_stop_count`
- `destination_stop_count`
