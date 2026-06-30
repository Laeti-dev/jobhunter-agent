from cv_model import Identity, Experience, Education, Project, SkillsSection, LanguagesSection

SECTIONS = [
    {
        "key": "identity",
        "label": "Identité",
        "is_list": False,
        "model": Identity,
        "min_user_messages": 5,
        "instructions": (
            "Collecte UNIQUEMENT ces 5 informations d'identité, une par une : "
            "(1) nom complet, "
            "(2) adresse email, "
            "(3) numéro de téléphone, "
            "(4) ville de résidence, "
            "(5) intitulé du métier recherché (ex : 'Data Scientist', 'AI Engineer Junior'). "
            "Tu ne peux ajouter [SECTION_DONE] QUE lorsque tu as reçu une réponse à ces "
            "5 informations précises — pas avant, même si l'utilisateur a répondu à certaines. "
            "NE parle PAS d'expériences passées, de formation, de compétences ou de projets — "
            "ces sujets seront abordés dans des sections séparées. "
            "Ne demande jamais l'âge, la date de naissance, la situation familiale, "
            "la nationalité ou une photo."
        ),
    },
    {
        "key": "experiences",
        "label": "expérience professionnelle",
        "article": "une",
        "is_list": True,
        "min_user_messages": 4,
        "item_model": Experience,
        "instructions": (
            "Pose des questions sur CETTE expérience professionnelle (une seule à la "
            "fois) : intitulé du poste, nom de l'entreprise, lieu, dates de début/fin, "
            "missions principales, réalisations concrètes (avec des chiffres si possible). "
            "Tu ne peux ajouter [ITEM_DONE] qu'après avoir collecté au minimum le poste, "
            "l'entreprise, les dates et au moins une mission ou réalisation. "
            "Tu peux proposer des soft skills déduites sous forme de question — ne les "
            "retiens que si l'utilisateur les confirme explicitement."
        ),
    },
    {
        "key": "education",
        "label": "formation",
        "article": "une",
        "is_list": True,
        "min_user_messages": 3,
        "item_model": Education,
        "instructions": (
            "Pose des questions sur CETTE formation (une seule à la fois) : diplôme, "
            "établissement, domaine d'étude, dates de début et de fin (ou 'en cours'). "
            "Tu ne peux ajouter [ITEM_DONE] qu'après avoir collecté le diplôme, "
            "l'établissement et le domaine d'étude."
        ),
    },
    {
        "key": "skills",
        "label": "Compétences techniques",
        "is_list": False,
        "min_user_messages": 2,
        "model": SkillsSection,
        "instructions": (
            "Pose des questions sur les compétences techniques (langages, outils, "
            "frameworks). N'inclus une soft skill QUE si elle a été confirmée "
            "explicitement par l'utilisateur dans une section précédente — sinon laisse "
            "la liste de soft skills vide."
        ),
    },
    {
        "key": "languages",
        "label": "Langues parlées",
        "is_list": False,
        "min_user_messages": 1,
        "model": LanguagesSection,
        "instructions": "Pose des questions sur les langues parlées et le niveau réel de chacune.",
    },
    {
        "key": "projects",
        "label": "projet",
        "article": "un",
        "is_list": True,
        "optional": True,
        "min_user_messages": 2,
        "item_model": Project,
        "instructions": (
            "Pose des questions sur CE projet (un seul à la fois) : titre, description, "
            "technologies utilisées. Tu ne peux ajouter [ITEM_DONE] qu'après avoir "
            "collecté le titre et la description du projet."
        ),
    },
]
