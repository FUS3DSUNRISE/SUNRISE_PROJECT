import re


STYLE_WORDS = {
    "modern", "classic", "minimalist", "rustic", "industrial", "vintage",
    "futuristic", "ornate", "scandinavian", "luxury", "simple", "stylized",
    "realistic", "cartoon", "medieval",
}

MATERIAL_WORDS = {
    "wood", "wooden", "metal", "metallic", "glass", "plastic", "fabric",
    "leather", "stone", "concrete", "ceramic", "rubber", "gold", "silver",
}

SIZE_WORDS = {
    "small", "medium", "large", "tiny", "huge", "giant", "mini", "wide",
    "narrow", "tall", "short", "low", "compact", "big",
}

DETAIL_WORDS = {
    "simple", "detailed", "realistic", "stylized", "highly detailed",
    "low poly", "ornate", "minimalist",
}

KNOWN_OBJECTS = {
    "table", "chair", "lamp", "cabinet", "desk", "bottle", "bookshelf",
    "shelf", "vase", "mirror", "sofa", "bed", "wardrobe", "stool", "mug",
    "plate", "bowl", "monitor", "laptop", "phone", "car", "truck", "bike",
    "console", "bench", "model", "robot", "statue", "sculpture",
}

BROAD_OBJECTS = {
    "table", "lamp", "cabinet", "console", "bench", "model", "shelf",
}

KNOWN_SUBTYPE_PHRASES = {
    "dining table", "coffee table", "bedside table", "desk lamp", "floor lamp",
    "table lamp", "game console", "console table", "control console",
    "park bench", "gym bench", "workbench",
}

MULTI_INTERPRETATION_TERMS = {
    "console": "Do you mean a game console, a console table, or a control console?",
    "bench": "Do you mean a park bench, a gym bench, or a workbench?",
    "model": "Do you mean a 3D object model, a miniature model, or a character model?",
}

CONFLICT_PAIRS = (
    ("minimalist", "ornate"),
    ("small", "giant"),
    ("tiny", "huge"),
    ("simple", "highly detailed"),
)

CLARIFICATION_DEFINITIONS = {
    "object_unspecified": {
        "priority": 10,
        "recommended_action": "ask_for_clarification",
        "question": "What specific object or item would you like me to generate?",
        "default_resolution": "If no object is explicit, choose the most common concrete object implied by the context and generate a simple first version.",
    },
    "object_subtype_ambiguous": {
        "priority": 35,
        "recommended_action": "ask_for_clarification",
        "question": "What specific subtype should be generated?",
        "default_resolution": "Choose the most common household or real-world subtype for the named object.",
    },
    "multi_interpretation_term": {
        "priority": 25,
        "recommended_action": "ask_for_clarification",
        "question": "Which meaning of the object do you intend?",
        "default_resolution": "Use the selected category or prompt context to choose the most likely interpretation.",
    },
    "category_prompt_conflict": {
        "priority": 15,
        "recommended_action": "ask_for_clarification",
        "question": "Should I follow the prompt text or the selected category?",
        "default_resolution": "Prioritize the user's free-text prompt over the selected category.",
    },
    "attribute_conflict": {
        "priority": 20,
        "recommended_action": "ask_for_clarification",
        "question": "Which constraint should be prioritized?",
        "default_resolution": "Prefer the object function and the most coherent visual constraint; ignore contradictory adjectives if needed.",
    },
    "item_count_ambiguous": {
        "priority": 30,
        "recommended_action": "ask_for_clarification",
        "question": "How many items should be included?",
        "default_resolution": "Use a standard composition, such as one main object or a common set size when a set is implied.",
    },
    "dimensions_missing": {
        "priority": 50,
        "recommended_action": "ask_for_clarification",
        "question": "What approximate size should it be?",
        "default_resolution": "Use medium, realistic real-world dimensions for the object category.",
    },
    "usage_context_missing": {
        "priority": 60,
        "recommended_action": "ask_for_clarification",
        "question": "What is it meant for or where will it be used?",
        "default_resolution": "Assume a general household or standard everyday use case.",
    },
    "shape_ambiguous": {
        "priority": 70,
        "recommended_action": "ask_for_clarification",
        "question": "What overall shape should it have?",
        "default_resolution": "Use a simple, stable, conventional shape for the object.",
    },
    "style_missing": {
        "priority": 80,
        "recommended_action": "ask_for_clarification",
        "question": "What visual style should it use?",
        "default_resolution": "Use a modern, clean style by default.",
    },
    "material_missing": {
        "priority": 90,
        "recommended_action": "proceed_with_defaults",
        "question": "What material should it be made of?",
        "default_resolution": "Use a sensible default material for the object category, such as wood for furniture and plastic or metal for manufactured objects.",
    },
    "detail_level_ambiguous": {
        "priority": 100,
        "recommended_action": "proceed_with_defaults",
        "question": "Should it be simple, stylized, realistic, or highly detailed?",
        "default_resolution": "Use a moderate level of detail suitable for a first generation.",
    },
}


def _tokens(text):
    return set(re.findall(r"[a-zA-Z]+", text.lower()))


def _has_number_or_dimension(text):
    return bool(re.search(r"\d|cm|mm|meter|metre|inch|inches|wide|height|depth|size", text.lower()))


def _case_payload(name, question=None):
    definition = CLARIFICATION_DEFINITIONS[name]
    return {
        "name": name,
        "priority": definition["priority"],
        "recommended_action": definition["recommended_action"],
        "clarification_question": question or definition["question"],
        "default_resolution": definition["default_resolution"],
    }


def _object_label_from_prompt(prompt_text, category):
    lowered = (prompt_text or "").lower()
    for phrase in sorted(KNOWN_SUBTYPE_PHRASES, key=len, reverse=True):
        if phrase in lowered:
            return phrase

    matches = []
    for object_name in KNOWN_OBJECTS:
        match = re.search(rf"\b{re.escape(object_name)}\b", lowered)
        if match:
            matches.append((match.start(), object_name))

    if matches:
        return sorted(matches)[0][1]

    if category and category != "Simple Objects":
        return category.lower()

    return "object"


def build_fallback_followup_message(prompt_text, category, ambiguity):
    if not ambiguity or not ambiguity.get("detected"):
        return None

    primary_case = (ambiguity.get("cases") or [{}])[0]
    question = primary_case.get("clarification_question") or "How would you like to refine it?"
    object_label = _object_label_from_prompt(prompt_text, category)

    return (
        f"I generated a first version of the {object_label} using sensible defaults. "
        f"To make it more accurate, {question}"
    )


class ClarificationRules:
    @staticmethod
    def analyze(prompt_text, selected_category=None, classification=None, is_clear=True, detector_reason=None):
        text = (prompt_text or "").strip()
        lowered = text.lower()
        words = _tokens(text)
        cases = []

        known_objects = words.intersection(KNOWN_OBJECTS)
        has_known_object = bool(known_objects)
        has_known_subtype = any(phrase in lowered for phrase in KNOWN_SUBTYPE_PHRASES)
        vague_object_request = bool(re.search(r"\b(something|anything|object|item|thing)\b", lowered))

        if not has_known_object and (not is_clear or vague_object_request):
            cases.append(_case_payload("object_unspecified"))

        family = (classification or {}).get("family")
        if selected_category and family and selected_category != "Simple Objects" and family != selected_category:
            cases.append(_case_payload("category_prompt_conflict"))

        for left, right in CONFLICT_PAIRS:
            if left in lowered and right in lowered:
                cases.append(_case_payload("attribute_conflict"))
                break

        for term, question in MULTI_INTERPRETATION_TERMS.items():
            if term in words:
                cases.append(_case_payload("multi_interpretation_term", question))
                break

        broad_objects = words.intersection(BROAD_OBJECTS)
        if broad_objects:
            object_name = sorted(broad_objects)[0]
            if not has_known_subtype:
                question = f"What kind of {object_name} do you want?"
                cases.append(_case_payload("object_subtype_ambiguous", question))

        if re.search(r"\b(set of|and)\b", lowered) and len(known_objects) >= 1:
            cases.append(_case_payload("item_count_ambiguous"))

        if has_known_object and not (_has_number_or_dimension(text) or words.intersection(SIZE_WORDS)):
            cases.append(_case_payload("dimensions_missing"))

        if words.intersection({"chair", "shelf", "desk", "table"}) and "for" not in words:
            cases.append(_case_payload("usage_context_missing"))

        if words.intersection({"vase", "mirror", "sofa", "lamp"}) and not words.intersection({"round", "oval", "rectangular", "square", "curved", "angular"}):
            cases.append(_case_payload("shape_ambiguous"))

        if has_known_object and not words.intersection(STYLE_WORDS):
            cases.append(_case_payload("style_missing"))

        if has_known_object and not words.intersection(MATERIAL_WORDS):
            cases.append(_case_payload("material_missing"))

        if words.intersection({"robot", "statue", "sculpture", "toy"}) and not words.intersection(DETAIL_WORDS):
            cases.append(_case_payload("detail_level_ambiguous"))

        unique_cases = {}
        for case in cases:
            unique_cases.setdefault(case["name"], case)

        ordered_cases = sorted(unique_cases.values(), key=lambda case: case["priority"])
        return {
            "detected": bool(ordered_cases),
            "handled_internally": True,
            "source_reason": detector_reason,
            "primary_case": ordered_cases[0]["name"] if ordered_cases else None,
            "cases": ordered_cases,
        }
