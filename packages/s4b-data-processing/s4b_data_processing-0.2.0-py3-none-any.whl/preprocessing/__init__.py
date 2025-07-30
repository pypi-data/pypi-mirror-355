__all__ = [
    "preprocessing",
    "CITIES_SETTINGS"
]

NSK_SETTINGS = {
    "class_mapping": {
        "Премиум": 1,
        "Элитный": 2,
        "Бизнес": 3,
        'Бизнес-': 3.5,
        "Комфорт": 4,
        "Эконом": 5
    },
    "default_class": 4,
    "is_log2_scale": False,
    "predictor_features": [
        "location",
        "district",
        "latitude",
        "longitude"
    ],
    "prediction_type": {
        "Интерполяция": 0,
        "Экстраполяция": 1,
    },
    "default_prediction_type": 0,
    "bbox": "74.312415,57.654077~86.551184,52.812563",
}

EKB_SETTINGS = {
    "class_mapping": {
        "Элитный": 1,
        "Бизнес": 2,
        "Комфорт": 3,
        "Эконом": 4
    },
    "default_class": 4,
    "is_log2_scale": False,
    "predictor_features": [
        "location",
        "district",
        "latitude",
        "longitude"
    ],
    "prediction_type": {
        "Интерполяция": 0,
        "Экстраполяция": 1,
    },
    "default_prediction_type": 0,
    "bbox": "60.326783, 56.985508~60.942358, 56.634953",
}

MSK_SETTINGS = {
    "class_mapping": {
        "Премиум": 1,
        "Элитный": 2,
        "Бизнес+": 3,
        "Бизнес": 4,
        "Бизнес-": 5,
        "Комфорт": 6,
        "Эконом": 7
    },
    "default_class": 6,
    "is_log2_scale": True,
    "predictor_features": [
        "location",
        "district",
        "latitude",
        "longitude"
    ],
    "prediction_type": {
        "Интерполяция": 0,
        "Экстраполяция": 1,
    },
    "default_prediction_type": 0,
    "bbox": "35.203810,54.167977~40.624199,56.982672",
}

CHB_SETTINGS = {
    "class_mapping": {
        "Комфорт": 1,
        "Эконом": 2
    },
    "default_class": 1,
    "is_log2_scale": False,
    "predictor_features": [
        "location",
        "district",
        "latitude",
        "longitude",
    ],
    "prediction_type": {
        "Интерполяция": 0,
        "Экстраполяция": 1,
        "История объявлений": 2,
    },
    "default_prediction_type": 0,
    "bbox": "55.007036, 61.151500",
}

CHB_OBL_SETTINGS = {
    "class_mapping": {
        "Комфорт": 1,
        "Эконом": 2
    },
    "default_class": 1,
    "is_log2_scale": False,
    "predictor_features": [
        "location",
        "district",
        "latitude",
        "longitude"
    ],
    "prediction_type": {
        "Интерполяция": 0,
        "Экстраполяция": 1,
    },
    "default_prediction_type": 0,
    "bbox": "55.007036, 61.151500",
}


CITIES_SETTINGS = {
    "nsk": NSK_SETTINGS,
    "ekb": EKB_SETTINGS,
    "msk": MSK_SETTINGS,
    "chb": CHB_SETTINGS,
    "chb_obl": CHB_OBL_SETTINGS,
    "new_msk": MSK_SETTINGS,
    "msk_obl": MSK_SETTINGS,
    "msk_united": MSK_SETTINGS,
    "msk_ckad": MSK_SETTINGS,
    "nsk_obl": NSK_SETTINGS,
    "nsk_united": NSK_SETTINGS
}
