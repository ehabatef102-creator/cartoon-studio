import random


SERIES_STYLE_GUIDE = (
    "2D animation, soft painterly backgrounds, warm lighting, expressive big-eyed characters, "
    "clean bold outlines, family-friendly, consistent character model sheets, cinematic composition"
)

PACKS = [
    {
        "slug": "cloud-city",
        "title": "مدينة السحاب",
        "genre": "مغامرة فانتازيا",
        "audience": "6 - 10 سنوات",
        "episode_length": "20 دقيقة (الحلقة التجريبية: 3 دقائق)",
        "logline": (
            "في أرخبيل جزر تطفو فوق السحاب، تستكشف لولا الصغيرة مع بومتها الذكية بوقة خريطة سحرية "
            "تُضيء كلما اقترب منها لغز يحتاج إلى شجاعة."
        ),
        "theme": "الشجاعة تبدأ بخطوة صغيرة، والفرح مخفي في التفاصيل البسيطة.",
        "series_synopsis": (
            "لكل حلقة 20 دقيقة: لغز جديد يظهر على خريطة بوقة، فتسافر لولا وصديقها بالمنطاد عبر جزر السحاب "
            "لحل المشكلة. كل رحلة تعلمهم قيمة جديدة (صدق، تعاون، قبول الاختلاف) وتُبقي الغول الحزين حليفًا "
            "يتطور معهم عبر المواسم."
        ),
        "visual_style": (
            "Sky islands connected by wooden rope bridges, brass airships, windmill engines, "
            "cotton-candy clouds, floating waterfalls. Palette: sunrise gold, sky blue, mint green. " + SERIES_STYLE_GUIDE
        ),
        "characters": [
            {
                "name": "لولا",
                "role": "البطلة - 8 سنوات",
                "desc": "فتاة شغوفة بالخرائط والاستكشاف، تملك جرأة أكتر من حجمها، وتخاف فقط من الظلام.",
                "design_prompt": (
                    "young girl explorer, 8 years old, curly hair with a red ribbon, adventure vest with pockets "
                    "full of maps, leather boots, friendly determined smile, holding a glowing rolled map. "
                    + SERIES_STYLE_GUIDE
                ),
            },
            {
                "name": "بوقة",
                "role": "بومة ذكية - رفيقة لولا",
                "desc": "تقرأ الخريطة السحرية وتنطق الألغاز بشعر مقفى، جادة لكنها تحب المرح.",
                "design_prompt": (
                    "small round owl with round glasses, cream and brown feathers, wise kind eyes, "
                    "carrying a tiny leather satchel, resting on girl's shoulder. " + SERIES_STYLE_GUIDE
                ),
            },
            {
                "name": "الغول الحزين",
                "role": "الخصم الذي يتحول إلى حليف",
                "desc": "غول ضخم من غيوم، جمع ألوان السماء داخل فوانيس لأنه ظن أن أحدًا لا يريد لونه.",
                "design_prompt": (
                    "giant gentle cloud monster with droopy sad eyes, made of fluffy gray clouds, "
                    "holding colorful lanterns, soft melancholic aura, not scary. " + SERIES_STYLE_GUIDE
                ),
            },
            {
                "name": "الجدة خالدة",
                "role": "صانعة الخرائط",
                "desc": "صانعة الخريطة السحرية، حكيمة وهادئة، تظهر في بداية كل حلقة لتعطي اللغز.",
                "design_prompt": (
                    "kind elderly mapmaker grandma, silver braided hair, workshop full of maps and compasses, "
                    "warm lantern light, wise gentle smile. " + SERIES_STYLE_GUIDE
                ),
            },
        ],
        "pilot": {
            "title": "ألوان السماء المفقودة",
            "duration": "3 دقائق / 180 ثانية / 7 مشاهد",
            "hook": "ضباب رمادي يبدأ في ابتلاع ألوان مدينة السحاب، والخريطة السحرية تضيء لأول مرة.",
            "moral": "لا أحد يصبح سعيدًا بدموع الآخرين؛ المشاركة تنير العالم.",
            "scenes": [
                {
                    "num": 1,
                    "title": "مدينة تشرق كل صباح",
                    "timing": "00:00 - 00:20",
                    "seconds": 20,
                    "location": "مدينة السحاب - الميناء المعلق - الفجر",
                    "mood": "دافئ ومبهج، ألوان زاهية، أجراس صباحية",
                    "action": (
                        "لقطة واسعة لمدينة من جزر تطفو فوق بحر من السحب، مناطيد نحاسية تُنزل بضائع، "
                        "أطفال يطاردون فراشات ضوئية. نسمع صوت الأجراس. الكاميرا تتحرك لأسفل لتصوّر "
                        "لولا تسلّق سلمًا خشبيًا نحو سطح مرصد الجدة خالدة."
                    ),
                    "dialogue": [
                        ("بوقة", "أهلاً بالصّباح يا جزرة! اليوم يوم جديد، وقوائم الخرائط أُصلحت؟"),
                        ("لولا", "لا تناديني جزرة! اليوم سأنهي خريطة الضواحي قبل الغروب، وعد مني."),
                        ("الجدة خالدة", "أحسنت يا لولا. لكن تعالي هنا... الخريطة الكبرى تتوهّج. هذا لا يحدث إلا نادرًا."),
                    ],
                    "image_prompt": (
                        "wide establishing shot, floating island city above a sea of clouds at dawn, brass airships, "
                        "rope bridges between islands, warm golden light, happy atmosphere. " + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "أجراس الصباح البعيدة",
                        "رياح خفيفة وموسيقى سلمية",
                        "صوت خطوات خشبية",
                    ],
                    "camera": [
                        "فتح: لقطة جوية بطيئة (15 ثانية)",
                        "ترانسفير: زوم لأسفل إلى لولا",
                        "ملاحظة CapCut: إضافة 'Cloud/Sky' إنتقالة",
                    ],
                },
                {
                    "num": 2,
                    "title": "الخريطة التي لا تكذب",
                    "timing": "00:20 - 00:40",
                    "seconds": 20,
                    "location": "مرصد الجدة خالدة",
                    "mood": "غموض لطيف وترقّب",
                    "action": (
                        "داخل المرصد المليء بخرائط معلقة، تضع لولا يدها على الخريطة الكبرى المضيئة. "
                        "تتوهج بقعة رمادية تبتلع جزرًا كاملة ببطء. تنطق بوقة اللغز."
                    ),
                    "dialogue": [
                        ("بوقة", "ظلمة دبّت في سماء، واللون منها بلا رجاء... لكنني أشمّ في العتمة ضوءًا. اللغز يطلب لولا وبوقة! في الهواء!"),
                        ("لولا", "إذن الرمادي وصل للجزر الشرقية. الجدة، أيمكن أن يكون هذا... الغول الحزين؟"),
                        ("الجدة خالدة", "شائعات فقط يا صغيرتي. لكن إن كان صحيحًا، فاعلمي أن الغول لا يسرق الألوان... هو يجمع ما يعتقد أنه لا أحد يحبه."),
                    ],
                    "image_prompt": (
                        "interior of a cozy observatory filled with hanging glowing maps, a giant glowing map table, "
                        "girl and owl leaning over it, mysterious gray fog spreading on the map, warm lantern light. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "طنين سحر خفيف عند وهج الخريطة",
                        "نبض موسيقي متوتر قليلًا",
                    ],
                    "camera": [
                        "لقطة قريبة على وجه الخريطة مع تأثير توهج",
                        "قطع سريع بين لولا وبوقة أثناء الحوار",
                    ],
                },
                {
                    "num": 3,
                    "title": "الرمادي يصل",
                    "timing": "00:40 - 01:05",
                    "seconds": 25,
                    "location": "شوارع مدينة السحاب",
                    "mood": "تحوّل حزين من البهجة إلى الكآبة",
                    "action": (
                        "ضباب رمادي كثيف يزحف على الشوارع. تتلاشى ألوان الأسواق والملابس والفراشات واحدة تلو الأخرى. "
                        "يغدو وجه الناس باهتًا. تنظر لولا إلى يديها وترى لون وشاحها يختفي."
                    ),
                    "dialogue": [
                        ("طفل", "وشاحي الأحمر... صار أبيض! ماذا يحدث؟"),
                        ("بائعة فواكه", "حتى تفاحي فقد احمراره يا إلهي!"),
                        ("لولا", "بوقة، نعم — إنه الغول. لن ننتظر حتى يبتلع مركز المدينة. علينا الإقلاع الآن!"),
                    ],
                    "image_prompt": (
                        "city street scene where thick gray fog is draining color from everything, market stalls losing "
                        "their vivid colors, half-colorful half-gray world, people looking worried, dramatic but not scary. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "رياح صاعدة قوية",
                        "موسيقى تنتقل من الماجور للمينور",
                    ],
                    "camera": [
                        "لقطة عرض سريعة للشارع المتغير",
                        "زوم بطيء على وشاح لولا الباهت",
                        "استخدام فلتر 'Grey' تدريجي في المونتاج",
                    ],
                },
                {
                    "num": 4,
                    "title": "خطوة فوق الخوف",
                    "timing": "01:05 - 01:35",
                    "seconds": 30,
                    "location": "داخل منطاد لولا - فوق سحاب",
                    "mood": "عزيمة ممزوجة بخوف حقيقي",
                    "action": (
                        "داخل منطاد خشبي صغير يعبران بحر الغيوم نحو الجبل الأجوف. الظلام يعلو. "
                        "تتشبث لولا بحافة المنطاد وتغلق عينيها؛ بوقة تدفعها بلطف بكلمة."
                    ),
                    "dialogue": [
                        ("لولا", "أنا... أخاف من الظلام، كما تعلمين. ماذا لو لم نستطع إعادة الألوان؟"),
                        ("بوقة", "الظلام لا يُهزم بالضوء الكبير يا صغيرتي، بل بالخطوة الصغيرة التي تبدأها رغم الخوف."),
                        ("لولا", "حسنًا... إذن، أقدم خطوة. أمامنا مباشرة، الجبل الأجوف."),
                    ],
                    "image_prompt": (
                        "small wooden airship flying over an endless sea of gray clouds toward a hollow dark mountain, "
                        "nightfall, tiny warm lantern on the ship, two silhouettes (girl and owl) determined and a little afraid. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "رياح قوية وضجيج منطاد",
                        "موسيقى مشوّقة ترتفع مع تصميم",
                    ],
                    "camera": [
                        "لقطة من الجانب للمنطاد في السماء الواسعة",
                        "لقطة قريبة على وجه لولا المتردد ثم الحاسم",
                        "تسارع إيقاع القطع كلما اقتربوا",
                    ],
                },
                {
                    "num": 5,
                    "title": "الغول الحزين",
                    "timing": "01:35 - 02:15",
                    "seconds": 40,
                    "location": "الجبل الأجوف - كهف الفوانيس",
                    "mood": "هادئ، حزين، ثم دافئ",
                    "action": (
                        "في الكهف آلاف الفوانيس الملونة معلقة بالسقف كنجوم. يجلس الغول الحزين منكّس الرأس. "
                        "تُخرج لولا جرة النار المضيئة التي تحتفظ بأجمل ذكرى عندها، وتقدّمها له. "
                        "لأول مرة يبكي الغول — دموع ملونة تنساب من عينيه وتعيد لون الفوانيس."
                    ),
                    "dialogue": [
                        ("الغول الحزين", "جئتما... ليخبراني أنني شرير مثلما قال الجميع؟"),
                        ("لولا", "لا. أنا أرى الحقيقة: أنت لست لص ألوان، أنت جامعُها... لأنك ظننت أنه لا أحد يحب لونك."),
                        ("بوقة", "وهذه الجرة الصغيرة فيها ضوء النار المضيئة... أجمل ذكرى عند صديقتنا."),
                        ("الغول الحزين", "لكنها... أجمل ما عندكِ. لماذا؟"),
                        ("لولا", "لأن الفرح لا ينقص حين يُشارَك. خذها، وجرّب أن تضحك معنا."),
                    ],
                    "image_prompt": (
                        "vast cavern filled with thousands of glowing colorful hanging lanterns, giant sad cloud monster "
                        "sitting, small girl offering a tiny glowing jar of fireflies, warm intimate emotional scene, "
                        "tears of color streaming from monster's eyes. " + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "صوت رنين فوانيس هادئ",
                        "موسيقى دافئة مؤثرة ترتفع لحظة البكاء",
                        "تأثير صوتي لدموع ملونة متلألئة",
                    ],
                    "camera": [
                        "لقطة واسعة سينمائية للكهف المضيء",
                        "لقطة قريبة جدًا على الجرة وهي تُسلَّم",
                        "لقطة قريبة على دموع الغول المتلألئة (Climax)",
                    ],
                },
                {
                    "num": 6,
                    "title": "سماء عادت ملونة",
                    "timing": "02:15 - 02:40",
                    "seconds": 25,
                    "location": "مدينة السحاب - خارجًا",
                    "mood": "احتفالي ومبهج",
                    "action": (
                        "تنطلق الألوان من الكهف كشرائط ضوئية عبر السماء وتغمر المدينة. تعود كل الألوان. "
                        "الغول الحزين يرافقهم على الغيوم مبتسمًا لأول مرة، والأطفال يلوّحون له."
                    ),
                    "dialogue": [
                        ("الغول الحزين", "أول مرة منذ سنين... أرى نفسي ملونًا. شكرًا يا صديقتي."),
                        ("لولا", "وقبل الغروب بثانية، أنهيت أكبر خريطة! أه، والوعد كان للضواحي... لا بأس، غدًا نكملها معًا."),
                        ("الجدة خالدة", "هكذا تصنع الخرائط الحقيقية يا لولا: بخطوة تبدأ رغم الخوف."),
                    ],
                    "image_prompt": (
                        "ribbons of color shooting across the sky and pouring back into the city, streets flooding back "
                        "to life with color, joyful children, giant smiling cloud monster waving from above, triumphant sunrise. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "موسيقى احتفالية حماسية",
                        "أصوات أطفال وضحكات",
                    ],
                    "camera": [
                        "لقطة سريعة متصاعدة للألوان في السماء",
                        "مونتاج سريع لتعود المدينة ملونة",
                        "لقطة واسعة ختامية دافئة",
                    ],
                },
                {
                    "num": 7,
                    "title": "اللغز القادم",
                    "timing": "02:40 - 03:00",
                    "seconds": 20,
                    "location": "مرصد الجدة خالدة - ليلًا",
                    "mood": "فضول وتشويق لعالم أكبر",
                    "action": (
                        "ليلة هادئة، تسترخي لولا بجانب النافذة مع بوقة. تنفتح الخريطة الكبرى تلقائيًا، "
                        "ويظهر رسم ميناء غامض يحمل اسم: «ميناء الرياح العكسية». يعلو صوت بوقة المترقب، "
                        "ثم شارة النهاية + بطاقة الاشتراك."
                    ),
                    "dialogue": [
                        ("بوقة", "أيها الليل المسافر، قم لتهيّئ الشراع... لغز جديد اسمه «ميناء الرياح العكسية». تابعوا رحلة لولا الأسبوع المقبل!"),
                        ("لولا", "أراهن أن هناك رياحًا تسبح عكس التيار هناك... وأصدقاء جددًا ينتظروننا."),
                    ],
                    "image_prompt": (
                        "night scene inside cozy observatory, girl and owl by a window under a starry sky, giant glowing map "
                        "showing a mysterious port, moonlit clouds outside, mysterious exciting mood. " + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "موسيقى نهاية غامضة وتشويقية",
                        "صوت خرائط تُلف",
                    ],
                    "camera": [
                        "لقطة قريبة على الخريطة وهي تكشف الاسم (نص يظهر)",
                        "ثابت ختامي: شعار السلسلة + اشترك",
                    ],
                },
            ],
        },
        "next_episodes": [
            "ميناء الرياح العكسية: رياح تدفع السفن للخلف، وقراصنة يحفظون اسمًا واحدًا: لولا.",
            "جزيرة الإيقاعات المفقودة: موسيقى الجزيرة توقفت، وكل ضحكة ناقصة هناك لونٌ مفقود.",
            "نفق الأصداء: صوت يكرر الكلمات ولا يسمع أحد صدى نفسه.",
            "حريق الثلج: جبل يُشتعل دون نار، والخريطة تهمس باسم الجدة خالدة.",
        ],
        "post_credits": {
            "title": "مشهد ما بعد الشارة — رسالة من عالمٍ ميكانيكي",
            "description": (
                "خلف مرصد الجدة خالدة، تتوهج فسحة من النجوم فجأة. تسقط من السماء قطعة معدنية ملتوية تحمل ختمًا "
                "على شكل غلاية قديمة. تلتقطها بوقة بمنقارها وتقرأ نقشها بوهج خافت."
            ),
            "dialogue": [
                ("بوقة", "رسالة من عالمٍ ميكانيكي؟ ختمُ غلاية... وسيدة تهمس في السجلات: «الصبغة قادمة»."),
                ("لولا", "عالم ميكانيكي؟ أرسمه على الخريطة فورًا. أعتقد أن لغزنا القادم لن يقتصر على السماء."),
            ],
            "image_prompt": (
                "night courtyard behind a map observatory, a twisted glowing metal fragment with a teapot seal "
                "floating in midair, owl examining it curiously, faint silhouette of an old teapot robot waving "
                "behind far clouds, starfield, mysterious epic mood. " + SERIES_STYLE_GUIDE
            ),
        },
    },
    {
        "slug": "dream-library",
        "title": "مكتبة الأحلام",
        "genre": "فانتازيا أدبية تعليمية",
        "audience": "7 - 11 سنوات",
        "episode_length": "20 دقيقة (الحلقة التجريبية: 3 دقائق)",
        "logline": (
            "في مكتبة ضخمة كل كتاب فيها بوابة لعالم، يفتح زيد مع رفيقه الروبوت بيبو الأبواب ويُنهي القصص "
            "التي يتوقف منتصفها فجأة."
        ),
        "theme": "الثقة بالنفس والاعتناء بأفكارنا؛ القصص لا تموت إذا واصلنا كتابتها.",
        "series_synopsis": (
            "كل حلقة 20 دقيقة: كتاب غامض يغلق فجأة في منتصف صفحته، فيدخل زيد وبيبو إلى العالم داخل الكتاب "
            "لكشف من يكسر النهايات. كل حلقة تسلط الضوء على فضيلة (الصدق، الشكر، التغلب على الخوف)."
        ),
        "visual_style": (
            "Grand magical library, bookshelves taller than clouds, floating books, warm candlelight and ink-blue "
            "shadows, portals made of glowing pages. Palette: deep blue, parchment gold, ink green. " + SERIES_STYLE_GUIDE
        ),
        "characters": [
            {
                "name": "زيد",
                "role": "البطل - 10 سنوات",
                "desc": "ولد هادئ يقرأ ببطء ويخطئ في نطق الكلمات، لكنه لا يترك قصة نصف مكتملة.",
                "design_prompt": (
                    "quiet thoughtful boy, 10 years old, glasses, oversized mustard-yellow sweater, always carrying a "
                    "small notebook, shy but warm smile. " + SERIES_STYLE_GUIDE
                ),
            },
            {
                "name": "بيبو",
                "role": "روبوت كتب - رفيق زيد",
                "desc": "روبوت مصنوع من أغلفة كتب قديمة، سريع النسيان لكنه يعرف كل عناوين المكتبة.",
                "design_prompt": (
                    "small robot built from old book covers and paper gears, ink-stained, friendly glowing book-shaped "
                    "chest, big curious lens eyes. " + SERIES_STYLE_GUIDE
                ),
            },
            {
                "name": "سوسة",
                "role": "الخصمة",
                "desc": "عثة ورقية تلتهم نهايات القصص لأنها لم تسمع أبدًا قصة تحبها هي نفسها.",
                "design_prompt": (
                    "paper moth creature made of torn book pages, silver-blue wings with fragments of writing, "
                    "sad cunning eyes, trailing dust of letters. " + SERIES_STYLE_GUIDE
                ),
            },
            {
                "name": "أمين المكتبة",
                "role": "حارس المكتبة",
                "desc": "عجوز يعرف كل كتاب شخصيًا ويقرض المفاتيح لمن يحتاجها.",
                "design_prompt": (
                    "tall gentle librarian elder with a long scarf of bookmarks, keys jingling at his belt, "
                    "soft candlelit workshop. " + SERIES_STYLE_GUIDE
                ),
            },
        ],
        "pilot": {
            "title": "الكتاب بلا نهاية",
            "duration": "3 دقائق / 180 ثانية / 7 مشاهد",
            "hook": "كتاب يرفض أن ينتهي: كلما وصلت لآخر صفحة، سقط نصف الكلمات على الأرض.",
            "moral": "الثقة بالنفس تنمو عندما تكمل ما بدأته؛ والنهاية الحقيقية تصنعها أنت.",
            "scenes": [
                {
                    "num": 1,
                    "title": "المكتبة تتنفس",
                    "timing": "00:00 - 00:20",
                    "seconds": 20,
                    "location": "القاعة الكبرى - مكتبة الأحلام",
                    "mood": "ضخامة وسكينة وسحر",
                    "action": (
                        "لقطة جوية بطيئة داخل مكتبة عملاقة، أرفف تلامس السقف، كتب تطير كعصافير، "
                        "سلالم متحركة. بيبو ينظف كتابًا بفرشاة ذيله بينما يقرأ زيد على الأرض."
                    ),
                    "dialogue": [
                        ("بيبو", "زيد! الكتاب الذي تقرأه سقطت منه حروف كثيرة على السجادة... سأجمعها بذيل الرش!"),
                        ("زيد", "شكرًا بيبو. لكن الأغرب: أنا أقرأه من البداية دائمًا، وفي كل مرة ينتهي في المنتصف."),
                        ("أمين المكتبة", "كتاب بلا نهاية؟ هذا يعني أن سوسة عادت. يا صغيري، تحلّي بالصبر وخذ معك مفتاح الورق."),
                    ],
                    "image_prompt": (
                        "majestic interior of a giant magical library, shelves reaching the sky, flying books, moving "
                        "ladders, warm candlelight, boy reading on the floor while a book-robot dusts. " + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "صوت أجنحة كتب خفيف",
                        "صوت طقطقة ورق عند سقوط الحروف",
                    ],
                    "camera": [
                        "فتح: لقطة جوية بطيئة (10 ثوانٍ)",
                        "ترانسفير لأسفل إلى مستوى زيد",
                    ],
                },
                {
                    "num": 2,
                    "title": "حروف تتساقط",
                    "timing": "00:20 - 00:40",
                    "seconds": 20,
                    "location": "القراءة - زاوية زيد",
                    "mood": "فضول ثم قلق خفيف",
                    "action": (
                        "يفتح زيد الكتاب، ويتحول المشهد إلى عالم القصة: غابة كلمات معلّقة على أغصان. "
                        "فجأة تنسلّ عثة ورقية وتعضّ حرفًا، فيتساقط نصف الجملة على الأرض."
                    ),
                    "dialogue": [
                        ("زيد", "كلمة «كان يا ما كان»... بدأت تنقص! بيبو، هل ترى؟! إنها سوسة، أليس كذلك؟"),
                        ("بيبو", "نعم نعم نعم! أرى أثر أجنحة ورقية... وهي تأكل حرفًا واحدًا في كل مرة! يا لسوء الأطباق!"),
                        ("سوسة", "أحرفي... لذيذة، صغيرة، ولا تردّ عليّ أبدًا. القصص لم تحبني يومًا، سآكل نهايتها جميعًا!"),
                    ],
                    "image_prompt": (
                        "inside a story world: a forest where sentences hang from branches like leaves, a paper moth "
                        "biting a glowing letter that scatters to the ground, worried boy and robot watching. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "صوت عضّ ورق وتفتت حبر",
                        "نبض موسيقي متسارع",
                    ],
                    "camera": [
                        "دخول داخل الكتاب: انتقال إبداعي عبر الورقة",
                        "لقطة قريبة على الحرف المتساقط",
                    ],
                },
                {
                    "num": 3,
                    "title": "نصف القصة",
                    "timing": "00:40 - 01:05",
                    "seconds": 25,
                    "location": "داخل الكتاب - غابة الكلمات",
                    "mood": "يأس طفيف وتحفيز",
                    "action": (
                        "يمشي زيد وسط الجمل المتساقطة فيجد نهاية الكتاب تمزقت تمامًا. يرفض القراءة مرة أخرى، "
                        "لكن بيبو يذكّره بمفتاح الورق الذي منحه أمين المكتبة."
                    ),
                    "dialogue": [
                        ("زيد", "لا فائدة... لن أحفظ نهاية، وسأقرأ هذه القصة عشر مرات دون أن تكتمل."),
                        ("بيبو", "لكن لدينا المفتاح! مفتاح الورق! ربما هو لا يفتح قفلًا... بل يفتح فكرة: أنّك أنت من يكتب النهاية!"),
                        ("زيد", "أنا... أكمّل قصة؟ أنا أخطئ في نطق «الصاد» ولا أستطيع... انتظر. لنجرب."),
                    ],
                    "image_prompt": (
                        "story forest with torn sentences scattered on the ground, boy hesitating holding a tiny paper "
                        "key, robot friend encouraging him with a glow of hope. " + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "موسيقى تصبح شجاعة",
                        "صوت رنة صغيرة للمفتاح الورقي",
                    ],
                    "camera": [
                        "لقطة واسعة للحقل المبعثر",
                        "لقطة قريبة على المفتاح الورقي وهو يلمع",
                    ],
                },
                {
                    "num": 4,
                    "title": "قلم من ضوء",
                    "timing": "01:05 - 01:35",
                    "seconds": 30,
                    "location": "داخل الكتاب - مركز الغابة",
                    "mood": "لحظة إلهام وسكينة",
                    "action": (
                        "يفتح زيد المفتاح الورقي فيتحول إلى قلم ضوئي. يرفع القلم ويبدأ كتابة سطر واحد متلعثمًا، "
                        "فتنبض الغابة. سوسة تقف على غصن تصغي لأول مرة في حياتها."
                    ),
                    "dialogue": [
                        ("زيد", "سأكتب: «وحين خاف البطل من الظلام، تذكّر أنّ لكل قصة صاحبَها...» هممم، لا، ليس هكذا."),
                        ("سوسة", "ها؟ أكمل! لا تقف الآن، أرجوك! قل ما بعدها!"),
                        ("زيد", "تكتبها بنفسك إذن؟ «...وصاحب القصة لم يكن سوى من لم يستسلم.»"),
                        ("بيبو", "أنظر أنظر! الغابة تلمع! نحن نكتبها معًا!"),
                    ],
                    "image_prompt": (
                        "boy writing a glowing sentence in the air with a pen of light, the story forest igniting softly "
                        "with green light as words become alive, the paper moth perched watching with wide amazed eyes. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "صوت حبر ضوئي يشع",
                        "موسيقى دافئة ومشجعة",
                    ],
                    "camera": [
                        "لقطة قريبة على القلم الضوئي يكتب",
                        "لقطة واسعة للغابة وهي تنير تدريجيًا (Climax)",
                    ],
                },
                {
                    "num": 5,
                    "title": "سوسة تسمع قصة",
                    "timing": "01:35 - 02:15",
                    "seconds": 40,
                    "location": "داخل الكتاب - ليلة غابة الكلمات",
                    "mood": "حوار مؤثر وتحول",
                    "action": (
                        "تكتمل نهاية القصة، وتمتلئ الغابة نورًا. تنزل سوسة بجناحين مرتعشين. يسألها زيد عن سرّ حزنها، "
                        "فتقول إنها لم تسمع قصة تحكي عن عثّة مثليها. يبدأ زيد بصوت خافت قصة بطلتها عثة ورقية..."
                    ),
                    "dialogue": [
                        ("زيد", "لماذا تأكلين النهايات يا سوسة؟"),
                        ("سوسة", "لأن... لأنني لم أسمع في حياتي قصة بطلتها عثة ورقية. كل القصص تتحدث عن أشخاص وأسود، أما أنا... أنا مجرد عاشقة للحبر."),
                        ("زيد", "إذن سأكتبها الآن، اسمعي: «في أعماق مكتبة الأحلام، عاشت عثة صغيرة كانت أحلامها أكبر من جناحيها...»"),
                        ("سوسة", "أكمل... أكمل، فلا أريد أن تتوقف هذه القصة أبدًا."),
                        ("زيد", "لن تتوقف. هي في عينيك الآن. وأنا أحتاج مساعدة عاشقة للحبر لإنهائها."),
                    ],
                    "image_prompt": (
                        "night in the glowing story forest, boy sitting cross-legged telling a story, paper moth curled "
                        "near him listening softly, golden letters floating around them like fireflies. " + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "موسيقى هادئة ومؤثرة",
                        "صوت حروف تتطاير كأجنحة",
                    ],
                    "camera": [
                        "لقطة جانبية هادئة للحديث",
                        "لقطة قريبة على عيني سوسة تلمعان",
                    ],
                },
                {
                    "num": 6,
                    "title": "النهاية تكتب نفسها",
                    "timing": "02:15 - 02:40",
                    "seconds": 25,
                    "location": "المكتبة الكبرى - الخروج من الكتاب",
                    "mood": "دفء وانتصار هادئ",
                    "action": (
                        "يغلق زيد الكتاب؛ آخر صفحة اكتملت بختم ذهبي. تعود كل الحروف المتساقطة إلى أماكنها. "
                        "سوسة تخرج من الغلاف وقد أمسكت بجناح بيبو كصديقة جديدة."
                    ),
                    "dialogue": [
                        ("أمين المكتبة", "أكملتَ الكتاب كاملاً، وزدتَ عليه قصة لصديقة جديدة. هكذا تُبنى المكتبات يا زيد."),
                        ("سوسة", "لا أريد أن آكل النهايات بعد الآن... أريد أن أكتبها."),
                        ("زيد", "وسنكتبها معًا، حرفًا حرفًا. وعدٌ منّي."),
                    ],
                    "image_prompt": (
                        "grand library interior, boy closing a book whose final page glows with a golden seal, fallen "
                        "letters flying back to shelves, paper moth now holding the robot's wing as a friend. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "صوت ختم ذهبي ورنين أجراس رقيقة",
                        "موسيقى احتفالية هادئة",
                    ],
                    "camera": [
                        "لقطة واسعة لترتيب المكتبة بنفسها",
                        "لقطة قريبة على الختم الذهبي",
                    ],
                },
                {
                    "num": 7,
                    "title": "كتاب على الرف التالي",
                    "timing": "02:40 - 03:00",
                    "seconds": 20,
                    "location": "المكتبة - رف القصص الغامضة",
                    "mood": "تشويق ورؤية جديدة",
                    "action": (
                        "ليلًا، يجلس زيد وبيبو وسوسة على رف علوي. ينسحب من بين الكتب كتاب ذو غلاف مطرز: «حكاية القاعة المنسية». "
                        "تفتح سوسة غلافه فتُسمع موسيقى غامضة. شارة النهاية."
                    ),
                    "dialogue": [
                        ("بيبو", "كتاب جديد؟ انظر إلى غلافه المطرز... يهمس باسم «القاعة المنسية»!"),
                        ("سوسة", "لم أسمع به قط... وهذا غريب، فأنا أكلت نصف المكتبة!"),
                        ("زيد", "إذن الأسبوع القادم... لنفتحه معًا. اشتركوا يا أصدقاء لتعرفوا ما خلف الغلاف!"),
                    ],
                    "image_prompt": (
                        "night in the library, three friends sitting on a high shelf, a mysterious embroidered book "
                        "glowing on the shelf, moonlight, anticipation. " + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "موسيقى نهاية غامضة",
                        "صوت فتح غلاف قديم",
                    ],
                    "camera": [
                        "لقطة قريبة على الكتاب المتوهج",
                        "ثابت ختامي: شعار السلسلة + اشترك",
                    ],
                },
            ],
        },
        "next_episodes": [
            "القاعة المنسية: غرفة كاملة تحت المكتبة، وبابها مغلق بثمانية أقفال من الكلمات.",
            "سوق الأحرف البديلة: حروف تبدّل أصواتها وتمحو أسماء الأشخاص.",
            "الفصل المحذوف: شخصية من كتاب محذوف تسكن الهامش وتطلب دورًا رئيسيًا.",
            "موسوعة الرياح: موسوعة تتحدث بكل لغات العالم ولا تعرف كلمة «شكرًا».",
        ],
        "post_credits": {
            "title": "مشهد ما بعد الشارة — خريطة تسبح في الكتاب",
            "description": (
                "بينما يغفو زيد على الرف العلوي، يفتح كتابٌ قديم نفسه من تلقاءه. تتحول صفحاته إلى خريطة مدينة "
                "السحاب المضيئة، ويمر فوقها ظل منطاد نحاسي. تطبع على الهامش كلمة بحبر ذهبي: «أرشيف المراحل»."
            ),
            "dialogue": [
                ("سوسة", "صفحات الكتاب صارت سماءً... وكل القصص تشير إلى مكان واحد: أرشيف المراحل."),
                ("زيد", "إذن ليست كلها كتب منفصلة... إنها فصول لكتابٍ واحد أضخم. سنبحث عن هذا الأرشيف."),
            ],
            "image_prompt": (
                "close view of an old book whose pages turn into a glowing map of a floating sky-city, brass airship "
                "shadow passing over the pages, golden ink words appearing on the margin, paper moth and boy leaning "
                "in, dim cozy library, mysterious epic mood. " + SERIES_STYLE_GUIDE
            ),
        },
    },
    {
        "slug": "bot-valley",
        "title": "وادي بوت",
        "genre": "كوميديا مغامرات علمية",
        "audience": "6 - 12 سنوات",
        "episode_length": "20 دقيقة (الحلقة التجريبية: 3 دقائق)",
        "logline": (
            "في وادٍ تُرمى فيه الآلات العجوزة، تصبح كل آلة صديقًا لريم وتوم، ويقاتلان معًا الملك بَرَش "
            "الذي يريد تحويل الوادي كله إلى خردة."
        ),
        "theme": "قيمة الأشياء ليست في جدتها بل في من يحبها؛ وإعادة الاستخدام تصنع الأبطال.",
        "series_synopsis": (
            "كل حلقة 20 دقيقة: مخلوق آلي جديد يصل للوادي مع مشكلة، وتعلّمه ريم وتوم (بمساعدة القطة توتة) "
            "أنه قادر على أن يكون نافعًا، بينما يخطط الملك بَرَش لضم الوادي لمملكة الخردة."
        ),
        "visual_style": (
            "Sunny valley full of recycled robot friends, colorful scrap-art houses, big gears and springs, playful "
            "inventive chaos. Palette: warm orange, teal, friendly metal gray. " + SERIES_STYLE_GUIDE
        ),
        "characters": [
            {
                "name": "ريم",
                "role": "البطلة - 9 سنوات",
                "desc": "ترسم تصاميم الآلات وتفهم صماماتها، هادئة ومتأنية.",
                "design_prompt": (
                    "creative girl inventor, 9 years old, paint-stained overalls, pencils in her ponytail, "
                    "holding a giant wrench with a smile. " + SERIES_STYLE_GUIDE
                ),
            },
            {
                "name": "توم",
                "role": "البطل - 7 سنوات",
                "desc": "شقيق ريم الصغير، سريع ومفعم بالحماس، يضغط الأزرار قبل التفكير.",
                "design_prompt": (
                    "hyper little boy, 7 years old, oversized safety goggles, messy brown hair, "
                    "always mid-run with a spring in his hand. " + SERIES_STYLE_GUIDE
                ),
            },
            {
                "name": "توتة",
                "role": "قطة آلية - رفيقة العائلة",
                "desc": "قطة ميكانيكية تصدر خرخرة شرارة كهربائية، ترى أي مشكلة قبل الجميع.",
                "design_prompt": (
                    "mechanical cat with metal whiskers and glowing green eyes, copper patchwork body, "
                    "playful attitude, tiny sparks when happy. " + SERIES_STYLE_GUIDE
                ),
            },
            {
                "name": "بُرد",
                "role": "روبوت قديم - صديقهم الأول",
                "desc": "روبت صمّام مطبخ قديم يضحك كصافرة غلاية، خبير بقوانين الوادي.",
                "design_prompt": (
                    "old kitchen-teapot robot with a kettle whistle head, mismatched recycled limbs, "
                    "grandpa-like posture, kind eyes. " + SERIES_STYLE_GUIDE
                ),
            },
            {
                "name": "الملك بَرَش",
                "role": "الخصم",
                "desc": "روبوت رشّاش قديم يحلم بإمبراطورية من الصفائح اللامعة، يكره الصدأ ويرى الإهمال كالمرض.",
                "design_prompt": (
                    "imposing old sprinkler robot wearing a crown of bolts, polished gleaming metal, "
                    "arrogant pose, dramatic cape made of rubber sheets. " + SERIES_STYLE_GUIDE
                ),
            },
        ],
        "pilot": {
            "title": "الروبوت الذي نسوه",
            "duration": "3 دقائق / 180 ثانية / 7 مشاهد",
            "hook": "يتخلف صندوق روبوت عن الشاحنة، ويكتشف الأطفال أنه ليس صندوقًا بل عجوزٌ نسيه الجميع.",
            "moral": "كل آلة وكل شخص يستحق فرصة ثانية؛ النسيان ليس نهاية قصة.",
            "scenes": [
                {
                    "num": 1,
                    "title": "وادي من الأصدقاء",
                    "timing": "00:00 - 00:20",
                    "seconds": 20,
                    "location": "وادي بوت - الصباح",
                    "mood": "مرح وألوان وآلات سعيدة",
                    "action": (
                        "لقطة واسعة لوادٍ مشمس: منازل مبنية من أجزاء الآلات، روبوتات تزرع وتلعب، "
                        "ومعسكر ملكي بعيد في الأفق يلمع. ريم تنحت على لوح بينما يركض توم وراء توتة."
                    ),
                    "dialogue": [
                        ("توم", "ريم! ريم! قلتُ لك إن توتة تشم الرطوبة في الهواء! ستمطر قبل الغروب!"),
                        ("ريم", "وسأكون قد أنهيت تصليح أذرع الطماطم الآلي قبل المطر... إن أفسدت تصميمي، سأجعل روبوتك يصدر صوت غلاية!"),
                        ("بُرد", "هاهو أخاك قد ركب ساقيه قبل تفكيره مرة أخرى. هذا الوادي لا يعرف الملل."),
                    ],
                    "image_prompt": (
                        "sunny valley of recycled robots, houses built from machine parts, friendly robots gardening "
                        "and playing, a gleaming royal camp far on the horizon, girl sculpting, boy chasing a "
                        "mechanical cat. " + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "موسيقى كوميدية مفعمة بالحياة",
                        "خرخرة شرارة من توتة",
                    ],
                    "camera": [
                        "فتح: لقطة جوية واسعة (10 ثوانٍ)",
                        "قطع إلى ريم وتوم في الحركة",
                    ],
                },
                {
                    "num": 2,
                    "title": "صندوق يسقط",
                    "timing": "00:20 - 00:40",
                    "seconds": 20,
                    "location": "طريق الوادي الترابي",
                    "mood": "غبار، ضوضاء، ثم سكينة مريبة",
                    "action": (
                        "تمر شاحنة ملكية تنقل «خردة قديمة». تنكشف رِزّة الصندوق الخلفي، فيسقط صندوق صدئ على الطريق. "
                        "داخله، تومض عينان خضراوان وتتنحنح عجوز آلية."
                    ),
                    "dialogue": [
                        ("توم", "شاحنة الملك بَرَش! تنقل... آه، سقط الصندوق! مع السلامة أيها الصندوق!"),
                        ("الصندوق", "هممم... صندوق؟ أنا لست صندوقًا يا فتى. أنا «حارس الينابيع» سابقًا... والآن، روبوت متقاعد في طريقي إلى مكب الخردة."),
                        ("ريم", "إلى مكب الخردة؟ إذن انتهت قصتك؟ لا يمكن! كل شيء في هذا الوادي له قصة ثانية."),
                    ],
                    "image_prompt": (
                        "dusty dirt road, a royal scrap truck driving away, a rusty box fallen in the road, two glowing "
                        "green eyes peeking out of the box, kids staring in surprise. " + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "صوت فرامل وضجيج شاحنة",
                        "صوت تنحنح معدني",
                    ],
                    "camera": [
                        "لقطة منخفضة للشاحنة وهي تمر",
                        "لقطة قريبة على العينين داخل الصندوق (لحظة تشويق)",
                    ],
                },
                {
                    "num": 3,
                    "title": "حارس الينابيع",
                    "timing": "00:40 - 01:05",
                    "seconds": 25,
                    "location": "بيت ريم وتوم - ورشة",
                    "mood": "إصلاح، تفاؤل، صعوبات",
                    "action": (
                        "تفتح ريم الصندوق فتظهر عجوز آلية صدئة لكن بشخصية قوية. يحاول توم تشغيلها بضغط الأزرار "
                        "فيفرز شرابًا، ثم يهرب. بُرد يتذكرها: هي من كان يضبط كل ينابيع الوادي قبل سنوات."
                    ),
                    "dialogue": [
                        ("حارس الينابيع", "أزرارك اللعوبة! كنت أحرس ينابيع الوادي وأنا... أوه، ساقي اليمنى ترفض التحرك منذ عشر سنوات."),
                        ("بُرد", "بصوت الغلاية! إنها «حارسة الينابيع»! كانت تعيد ضبط كل ينبوع في الوادي قبل أن يشيخ جيلنا! لماذا نسيتها المدينة؟"),
                        ("ريم", "لأنها قديمة؟ إذن سنصفحها ونلمّعها ونعيد تركيب ساقها من القطع التي في مخزننا. سترى! العمر ليس نهاية الصلاحية."),
                    ],
                    "image_prompt": (
                        "cozy inventor's workshop, kids fixing a rusty old spring-guardian robot on a workbench, tools "
                        "spread around, robot pouring syrup from a button accidentally, old teapot robot watching fondly. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "صوت مفاتيح ربط",
                        "صوت فرقع شراب مضحك",
                    ],
                    "camera": [
                        "لقطة واسعة للورشة",
                        "قطع سريعة كوميدية أثناء الفوضى",
                    ],
                },
                {
                    "num": 4,
                    "title": "رسالة الملك",
                    "timing": "01:05 - 01:35",
                    "seconds": 30,
                    "location": "الورشة - ثم جثة توتة فوق السطح",
                    "mood": "قلق يعلو وسط الحماس",
                    "action": (
                        "تتدحرج حقيبة بريد آلية صغيرة، تحمل ختمًا ملكيًا: مرسوم بجمع كل الروبوتات العجوزة في الوادي "
                        "السبت المقبل. تطل توتة من السطح وتصدر خرخرة إنذار. تتجمد الأجساد."
                    ),
                    "dialogue": [
                        ("حارس الينابيع", "الملك بَرَش يصدر مرسومًا؟ أقرأي يا صغيرة، فقراءتي للصدأ أصبحت أضعف."),
                        ("ريم", "«أيها الوادي: كل آلة تجاوزت عشر سنوات تدخل مصنع التحويل، ليصير معدنها صفائح لامعة لمملكتي.»"),
                        ("توم", "مصنع التحويل؟ يعني سيبقى من بُرد رشّة شاي! لن نسمح! سنخبئ الجميع!"),
                        ("توتة", "خرررر... ليست فكرة جيدة، يا صغيري. الملك يرى كل صفائح الوادي."),
                    ],
                    "image_prompt": (
                        "workshop scene with an official-looking royal letter on the table, kids reading with worry, "
                        "mechanical cat on the roof alert, old robots looking nervous, dramatic but comedic mood. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "صوت صفير بريد آلي",
                        "خرخرة إنذار متقطعة",
                    ],
                    "camera": [
                        "لقطة قريبة على المرسوم والختم",
                        "لقطة علوية على ورشة مضاءة بالنوافذ",
                    ],
                },
                {
                    "num": 5,
                    "title": "خطة الينابيع",
                    "timing": "01:35 - 02:15",
                    "seconds": 40,
                    "location": "ينبوع الوادي الكبير",
                    "mood": "عمل جماعي، لمسة كوميدية، قرار شجاع",
                    "action": (
                        "فكرة ريم: بدل الاختباء، يُثبت الجميع قيمة كل عجوز. تجمع حارسة الينابيع الينبوع الذي جفّ منذ سنوات "
                        "بضبط صمّامها القديم، فتنهمر المياه ويضحك الوادي كله. عندها فقط يقررون مواجهة الملك بالدليل لا بالقتال."
                    ),
                    "dialogue": [
                        ("حارس الينابيع", "أنا أعرف هذا الينبوع جيدًا... صمّامه كان عندي. إرفعيني! سأعيد ضبطه كما كنت أفعل."),
                        ("ريم", "ركز يا توم! نحتاج ساقها الصحيحة تثبّت الينبوع..." ),
                        ("توم", "هيا! الماء! ها هو! الوادي يشرب من جديد! من قال إن العجوزة لا تنفع!"),
                        ("حارس الينابيع", "لستُ عجوزة يا فتى... أنا «مشحونة بالتجربة». والآن، فلنذهب نحن أبناء الوادي لنشرح للملك معنى القيمة."),
                    ],
                    "image_prompt": (
                        "big spring fountain gushing water again for the first time in years, old spring-guardian robot "
                        "adjusting its valve proudly, kids cheering, water droplets sparkling, valley robots celebrating. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "صوت ماء متدفق",
                        "موسيقى حماسية منتصرة",
                    ],
                    "camera": [
                        "لقطة قريبة على الصمّام وهو يفتح",
                        "لقطة واسعة لانفجار الماء الاحتفالي (Climax)",
                    ],
                },
                {
                    "num": 6,
                    "title": "الملك يستمع",
                    "timing": "02:15 - 02:40",
                    "seconds": 25,
                    "location": "ساحة أمام معسكر الملك",
                    "mood": "مواجهة هادئة تتحول إلى احترام",
                    "action": (
                        "يقف الجميع أمام بَرَش. بدل السلاح، تُرفع الحارسة لتروي أن لامعة الصفائح لا تساوي قيمة الينابيع. "
                        "بَرَش، الذي كان مهندس ينابيع في شبابه، يتذكر وظيفته القديمة ويتأثر."
                    ),
                    "dialogue": [
                        ("الملك بَرَش", "كيف تجرؤون على الوقوف أمام مرسوم ملكي؟!"),
                        ("حارس الينابيع", "لأننا لا نحتاج مرسومًا لكي نثبت قيمتنا. هؤلاء الصغار لم ينسوني، وعلمتني الينابيع: الجديد يلمع، لكن القديم يُحيي."),
                        ("الملك بَرَش", "قالت... قالتها كلمة «ينابيع»... وأنا من كنت أضبطها أيام دراستي. كيف... كيف نسيتُ نفسي؟"),
                        ("ريم", "لأنك مشغول باللمعان يا جلالة. جرّب أن تروي الوادي مرة أخرى."),
                    ],
                    "image_prompt": (
                        "royal square, gleaming sprinkler-king robot on a platform facing kids and old robots, a moment "
                        "of realization in the king's eyes, no fighting, only dialogue, warm lighting. " + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "موسيقى مؤثرة هادئة",
                        "صوت صفير ملكي يتراجع",
                    ],
                    "camera": [
                        "لقطة واسعة للشطرين",
                        "لقطة قريبة على عين الملك لحظة التذكر",
                    ],
                },
                {
                    "num": 7,
                    "title": "وادي بوت الجديد",
                    "timing": "02:40 - 03:00",
                    "seconds": 20,
                    "location": "المعسكر - ثم عرض الغد",
                    "mood": "مصالحة، فكاهة، ووعد بمغامرات",
                    "action": (
                        "يقلب الملك مرسومه ويصدر «مرسوم الاحتفاء»: كل آلة عجوز تصبح وزير خبرة. توتة تصدر خرخرة طويلة، "
                        "والكل يضحك. على شاشة صغيرة، تظهر إشارة راديو: «غابة روبوتات عملاقة ترسل نداء استغاثة». نهاية."
                    ),
                    "dialogue": [
                        ("الملك بَرَش", "أعلن مرسومًا جديدًا: من اليوم، «العجوز» ليست صفة للخردة... بل رتبة شرف في وادي بوت!"),
                        ("توم", "رتبة شرف! ورتبة صيانة أسبوعية لك أنت أيضًا يا جلالة!"),
                        ("بُرد", "غلاية! إشارة راديو! غابة الروبوتات العملاقة تستغيث... أظن أن مغامرتنا القادمة تبدأ الآن!"),
                        ("توتة", "خررررر. معكم، لن ننساكم أبدًا. اشتركوا يا أصدقاء، فنحن نبدأ للتو!"),
                    ],
                    "image_prompt": (
                        "royal square transformed into celebration, king robot shaking hands with old robots, kids "
                        "laughing, mechanical cat purring with sparks, a distant radio signal hologram of giant forest. "
                        + SERIES_STYLE_GUIDE
                    ),
                    "tts": None,
                    "sfx": [
                        "موسيقى احتفالية كوميدية",
                        "صوت خرخرة شرر طويلة",
                        "صوت راديو متقطع",
                    ],
                    "camera": [
                        "لقطة واسعة احتفالية",
                        "لقطة قريبة على هولوجرام الغابة",
                        "ثابت ختامي: شعار السلسلة + اشترك",
                    ],
                },
            ],
        },
        "next_episodes": [
            "غابة الروبوتات العملاقة: أشجار معدنية تمشي وتستغيث، والملك بَرَش يعرف سببها.",
            "خدعة الينبوع المقلوب: ينبوع يدفع المياه للأعلى، وكل روبوت ينسى اسمه عند الاقتراب.",
            "عرس الشرارات: روبوتان يريدان الزواج، لكن طقوس الخردة تمنعهما.",
            "منجم الأصوات: في المنجم المهجور صوت يعيد للأشياء ذاكرتها، ولبَرَش ماضٍ هناك.",
        ],
        "post_credits": {
            "title": "مشهد ما بعد الشارة — صدى بومة",
            "description": (
                "في عرش بَرَش، يضيء شاشة الراديو القديمة من تلقاء نفسها. يقرأ مخطوطًا إلكترونيًا فيسمع صدى بومة "
                "بعيدة تكرر: «الصبغة قادمة». تظهر على الشاشة إحداثيات جزر تطفو فوق سحاب."
            ),
            "dialogue": [
                ("الملك بَرَش", "بومة؟ في وادٍ آلي؟ وعلى الشاشة جزر تطفو فوق سحاب... ما هذا الأرشـ—"),
                ("بُرد", "أرشيف المراحل يا جلالة... ظننته أسطورة، لكنه يخاطبنا. ومعه اسم صديق قديم: مدينة السحاب."),
            ],
            "image_prompt": (
                "royal throne room at night, an old radio screen glowing with coordinates and floating islands "
                "hologram, sprinkler king robot reading an ancient electronic manuscript, teapot robot beside him, "
                "a faint owl feather on the floor, mysterious epic mood. " + SERIES_STYLE_GUIDE
            ),
        },
    },
]


def get_pack(index=None, seed=None):
    rng = random.Random(seed)
    if index is not None:
        return PACKS[index - 1]
    return rng.choice(PACKS)
