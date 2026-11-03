# Bibliothèque de Monsieur Vass

Éléments réutilisés dans chaque montage (les scripts les copient automatiquement dans leur dossier de travail).

| Fichier | Quoi | Réglage |
|---|---|---|
| `transitions/burn-transition-12.mp4` | « Burn Transition » (lumière qui brûle), 0,67 s, 2560×1440, avec son | fusion « screen » ; pic lumineux à l'image 11 (0,37 s), ensuite noir |
| `sfx/riser-metallic-transition.mp3` | « SFX – Riser Metallic Transition », montée de suspense, 5,3 s | pic à 2,95 s : le caler sur la grosse révélation |
| `sfx/cash-ding.mp3` | clochette de caisse « ding » (son « matricula »), 2,5 s | pic à 0,4 s : à caler sur un chiffre, un prix, « 140 MILLIONS » ; gain 0,5–0,6 |
| `sfx/money-counter.mp3` | compteur de billets qui défilent, 4,9 s | partie régulière dès 0,6 s ; sous un compteur d'argent, coupé à la longueur voulue avec fondu ; gain 0,9 |
| `sfx/goal-crowd.mp3` | foule qui explose sur un but, 2,7 s | pic à 0,5 s ; sur un but, une célébration, une grosse annonce sport ; gain 0,3–0,45 sous la voix |
| `sfx/synth-whoosh.wav` | whoosh de coupe (bruit rose filtré) | gain 0,1–0,25 |
| `sfx/synth-hit.wav` | impact grave 52 Hz pour les titres 3D | gain 0,45 |
| `sfx/synth-click.wav` | clic de machine à écrire | gain 0,25, un par lettre |
| `backgrounds/grid-paper-red.png`, `grid-paper-blue.png` | grille papier rouge / bleue plein écran 1080×1920, tirée de ses bandeaux papier | fonds d'écrans texte, en alternance avec le dégradé rouge et le noir quadrillé (`kali_fx.bg('paper_red'|'paper_blue')`, `bg_for(n)`) |
| `backgrounds/red-gradient.mp4` | « Copy of Red », dégradé rouge animé, 1080×1920, 12,6 s | fond des écrans texte façon Kali Muscle (en boucle), avec grille et étincelles |
| `overlays/torn-paper-banner-red.mp4` | bandeau papier déchiré, grille rouge, sur fond vert, 1080×1920, 25,5 s, muet | incrustation `colorkey=0x1DDA0B:0.25:0.08` ; le papier arrive en se dépliant (0–0,3 s), couvre le haut jusqu'à y ≈ 640 ; vers 9,8 s la grille passe au noir. Zone pour un titre néon |
| `overlays/torn-paper-banner-blue.mp4` | même bandeau, grille bleue | idem |
| `overlays/eye-tear-paper.mp4` | œil (maquillage violet) qui apparaît en **déchirant du papier**, fond vert, 1080×1080, 3 s, muet | `colorkey=0x40F800:0.3:0.1` ; déchirure 0–1,2 s puis tenu. Pour « regardez bien », un regard, un mystère |
| `overlays/eye-shatter.mp4` | œil bleu qui se reconstitue **en éclats**, fond vert, 1080×1080, 3 s, muet | `colorkey=0x40F800:0.3:0.1` ; éclats 0–1,6 s puis tenu |
| `overlays/hand-tear-paper.mp4` | **main qui traverse le papier** et se tend, fond vert, 1080×1080, 3 s, muet | `colorkey=0x40F800:0.3:0.1` ; 0–1,2 s ; pour « je vous tends la main », appel au soutien, un artiste qui débarque |
| `overlays/tape-strip-flat.mp4` | **morceau de scotch** qui se colle, fond vert, 1080×1920, 5 s, muet | `colorkey=0x00AF3F:0.25:0.08` ; arrive en 0,3 s, zone x 369–710, y 863–1055 ; à poser sur le bord d'une photo ou d'une pochette (effet collage). Lire sans `-ss` avant l'entrée (seek = image vide) |
| `overlays/tape-strip-wide.mp4` | scotch plus large et froissé | `colorkey=0x00AF3F:0.25:0.08` ; zone x 306–753, y 853–1070 ; idem |
| `3d/lightning-white.png`, `lightning-orange.png`, `lightning-gradient.png`, `lightning-gold.png` | éclairs 3D (blanc, orange, dégradé violet, or), PNG transparents 2000×2000 | « pop » sur les mots forts (ex. « BOOM », « C'EST MORT »), en coin ou derrière un titre |
| `3d/paper-peel-dark.png` | carte sombre au coin replié, PNG transparent | fond de carte pour un texte ou une pochette |

## Extraits classés par pilier (`extraits/`)

| Fichier | Pilier | Contenu |
|---|---|---|
| `extraits/musique/tv-big-up-monsieur-vass.mp4` | MUSIQUE | Émission TV (repost TikTok, image 16:9 au centre, y 318–642) : collab avec Z de 13 Block, « un gros big up à Monsieur Vass, c'est un influenceur TikTok » à 13,5 s |
| `extraits/musique/sortie-concert-nuit.mp4` | MUSIQUE | Sortie de concert de nuit avec les artistes, photo de groupe à 9 s |
| `extraits/musique/dopelym-live-afrique.mp4` | MUSIQUE | Dopelym en live en Afrique (foule, fumigènes), 0–20 s ; filigrane TikTok : recadrer 15 % de chaque côté |
| `extraits/musique/dopelym-clip-voiture.mp4` | MUSIQUE | Extrait de clip de Dopelym (voitures, lui dans la voiture), 0–22 s |
| `extraits/musique/kadja-freestyle-kordial-3.mp4` | MUSIQUE | Teaser carré 576×576 du clip « Freestyle Kordial 3 » de Kadja, titre à 11–13,5 s ; filigrane @kadjaofficiel en haut à gauche puis en bas à droite (flouter + créditer) |
| `extraits/musique/philipayne-thb-deux-mondes.mov` | MUSIQUE | Teaser vertical 720×1280 de « Deux Mondes » (Philipayne × THB), titre à 5–7 s, « disponible mercredi 18h » à 15 s ; pas de filigrane |
| `extraits/culture/tapis-rouge-evenement.mp4` | CULTURE | Tapis rouge d'un événement, sans parole |
| `extraits/culture/interview-monsieur-vass.mp4` | CULTURE | Son interview (image 16:9 au centre) : « je vais continuer à faire du contenu » (0–3,3 s), vidéos réactions, New Wave |
| `extraits/sport/yan-diomande-but-montage.mov` | SPORT | Montage du but de Yan Diomandé (Real Madrid, n°25) : frappe 0,6–4 s, célébration 6 s, gros plans 19–22 s ; filigrane TikTok : recadrer à 78 % |
| `extraits/sport/yan-diomande-but-tribune.mp4` | SPORT | Le même match filmé en tribune, célébration 14–18 s |
| `extraits/sport/cote-divoire-coupe-du-monde.mp4` | SPORT | Sa vidéo Côte d'Ivoire / Coupe du monde : Infantino, Éléphants, poule avec l'Allemagne, « restez concentrés » à 36,9 s |

Logo : `showreel/assets/logos/monsieur-vass.png`.
