# Bibliothèque de Monsieur Vass

Éléments réutilisés dans chaque montage (les scripts les copient automatiquement dans leur dossier de travail).

| Fichier | Quoi | Réglage |
|---|---|---|
| `transitions/burn-transition-12.mp4` | « Burn Transition » (lumière qui brûle), 0,67 s, 2560×1440, avec son | fusion « screen » ; pic lumineux à l'image 11 (0,37 s), ensuite noir |
| `sfx/riser-metallic-transition.mp3` | « SFX – Riser Metallic Transition », montée de suspense, 5,3 s | pic à 2,95 s : le caler sur la grosse révélation |
| `sfx/cash-ding.mp3` | clochette de caisse « ding » (son « matricula »), 2,5 s | pic à 0,4 s : à caler sur un chiffre, un prix, « 140 MILLIONS » ; gain 0,5–0,6 |
| `sfx/money-counter.mp3` | compteur de billets qui défilent, 4,9 s | partie régulière dès 0,6 s ; sous un compteur d'argent, coupé à la longueur voulue avec fondu ; gain 0,9 |
| `sfx/goal-crowd.mp3` | foule qui explose sur un but, 2,7 s | pic à 0,5 s ; sur un but, une célébration, une grosse annonce sport ; gain 0,3–0,45 sous la voix |
| `sfx/beep-censure.mp3` | bip de censure continu (1 kHz type télé), son de 0,09 à 4,5 s | couper à la longueur du mot à masquer (gros mot, nom à cacher, chiffre secret) ; ou bip très court sur un « ding » d'info ; gain 0,3–0,4 |
| `sfx/camera-shutter-long.mp3` | déclencheur d'appareil photo (clic + armement), son 0,29–1,25 s, pic à 0,74 s | sur l'apparition d'une photo, d'une pochette, d'un flash blanc ; **source à +1,6 dBFS → gain 0,4–0,5 max** |
| `sfx/camera-shutter-short.mp3` | clic d'appareil photo sec, 0,34 s, pic à 0,21 s | sur chaque photo d'une rafale, galerie d'artistes, capture d'écran ; gain 0,5–0,7 |
| `sfx/sparkle.mp3` | scintillement magique, deux occurrences : 0,75–1,84 s et 4,29–5,38 s (pic 4,36 s) | sur un objet doré, un disque d'or/certification, un cœur, une révélation « brillante » ; prendre l'une des deux parties ; gain 0,3–0,4 |
| `sfx/whoosh-1.mp3` | whoosh ample, son 0,31–0,80 s, pic 0,42 s | grosses transitions, entrée d'une carte ou d'un titre 3D ; caler le pic sur la coupe (placer à t − 0,42) ; gain 0,25–0,35 |
| `sfx/whoosh-2.mp3` | whoosh court, 0,07–0,37 s, pic 0,13 s | coupes rapides, mots qui apparaissent ; gain 0,2–0,3 |
| `sfx/whoosh-3.mp3` | whoosh très sec, 0,21–0,38 s, pic 0,26 s | zooms / punch-in, pop d'image ; gain 0,2–0,3 |
| `sfx/whoosh-4.mp3` | whoosh court, 0,04–0,42 s, pic 0,08 s | glissement de texte, changement de fond ; gain 0,2–0,3 |
| `sfx/uhh.mp3` | « uhh » voix (réaction hésitante / malaise), 0,64–0,93 s, pic 0,74 s | moment gênant, info douteuse, « hmm… vraiment ? » ; **source très forte (+7,7 dBFS décodé) → gain 0,15–0,25** |
| `sfx/synth-whoosh.wav` | whoosh de coupe (bruit rose filtré) | gain 0,1–0,25 |
| `sfx/synth-hit.wav` | impact grave 52 Hz pour les titres 3D | gain 0,45 |
| `sfx/synth-click.wav` | clic de machine à écrire | gain 0,25, un par lettre |
| `backgrounds/grid-paper-red.png`, `grid-paper-blue.png` | grille papier rouge / bleue plein écran 1080×1920, tirée de ses bandeaux papier | fonds d'écrans texte, en alternance avec le dégradé rouge et le noir quadrillé (`kali_fx.bg('paper_red'|'paper_blue')`, `bg_for(n)`) |
| `backgrounds/red-gradient.mp4` | « Copy of Red », dégradé rouge animé, 1080×1920, 12,6 s | fond des écrans texte façon Kali Muscle (en boucle), avec grille et étincelles |
| `overlays/torn-paper-banner-red.mp4` | bandeau papier déchiré, grille rouge, sur fond vert, 1080×1920, 25,5 s, muet | incrustation `colorkey=0x1DDA0B:0.25:0.08` ; le papier arrive en se dépliant (0–0,3 s), couvre le haut jusqu'à y ≈ 640 ; vers 9,8 s la grille passe au noir. Zone pour un titre néon |
| `overlays/torn-paper-banner-blue.mp4` | même bandeau, grille bleue | idem |
| `overlays/eye-tear-paper.mp4` | œil (maquillage violet) qui apparaît en **déchirant du papier**, fond vert, 1080×1080, 3 s, muet | `colorkey=0x40F800:0.3:0.1` ; déchirure 0–1,2 s puis tenu. Pour « regardez bien », un regard, un mystère |
| `overlays/eye-shatter.mp4` | œil bleu qui se reconstitue **en éclats**, fond vert, 1080×1080, 3 s, muet | `colorkey=0x40F800:0.3:0.1` ; éclats 0–1,6 s puis tenu |
| `overlays/eye-paper-unfold.mp4` | **boule de papier froissé qui se déplie en œil** (iris gris-vert), puis l'œil regarde autour, fond vert, 2000×2000, 20 s, muet | `colorkey=0x18FF07:0.3:0.1` ; dépliage 0–0,6 s puis tenu ; pour « regardez bien », un regard, surveiller, un mystère |
| `overlays/hand-tear-paper.mp4` | **main qui traverse le papier** et se tend, fond vert, 1080×1080, 3 s, muet | `colorkey=0x40F800:0.3:0.1` ; 0–1,2 s ; pour « je vous tends la main », appel au soutien, un artiste qui débarque |
| `overlays/tape-strip-flat.mp4` | **morceau de scotch** qui se colle, fond vert, 1080×1920, 5 s, muet | `colorkey=0x00AF3F:0.25:0.08` ; arrive en 0,3 s, zone x 369–710, y 863–1055 ; à poser sur le bord d'une photo ou d'une pochette (effet collage). Lire sans `-ss` avant l'entrée (seek = image vide) |
| `overlays/tape-strip-wide.mp4` | scotch plus large et froissé | `colorkey=0x00AF3F:0.25:0.08` ; zone x 306–753, y 853–1070 ; idem |
| `3d/lightning-white.png`, `lightning-orange.png`, `lightning-gradient.png`, `lightning-gold.png` | éclairs 3D (blanc, orange, dégradé violet, or), PNG transparents 2000×2000 | « pop » sur les mots forts (ex. « BOOM », « C'EST MORT »), en coin ou derrière un titre |
| `3d/paper-peel-dark.png` | carte sombre au coin replié, PNG transparent | fond de carte pour un texte ou une pochette |
| `3d/money-stack-teal.png`, `money-stack-pink.png`, `money-stack-gold.png`, `money-stack-white.png` | liasse de billets 3D avec bande « $ » (turquoise/orange, rose-violet dégradé, gris/or, blanc mat), PNG transparents 2000×2000 | argent, cachet, contrat, streams qui rapportent, « 140 MILLIONS » ; or = luxe, blanc = schéma sobre ; avec `sfx/cash-ding.mp3` |
| `3d/heart-gold.png` | cœur 3D doré, PNG transparent 2000×2000 | amour du public, « merci la famille », hommage, likes |
| `3d/music-note-gold.png`, `music-note-red.png`, `music-note-gradient.png` | note de musique 3D (or, rouge-orange, dégradé jaune-violet), PNG transparents 2000×2000 | pilier MUSIQUE : nouveau son, single, playlist, « à écouter » ; avec `sfx/sparkle.mp3` pour la dorée |
| `3d/wifi-red.png`, `wifi-gradient.png` | signal wifi 3D (rouge-orange, dégradé violet), PNG transparents 2000×2000 | live, en ligne, internet, réseaux sociaux, « ça a buzzé », streaming |
| `icons/groupe-celebration-trinque.png` | pictogramme blanc lumineux : 3 personnes qui trinquent / célèbrent, PNG transparent 1080×1080 | victoire, sortie d'album, certification, fête, release party |
| `icons/duo-amis-rire.png` | 2 amis qui rigolent épaule contre épaule | collab, featuring, amitié entre artistes, « des frères » |
| `icons/equipe-solidaire-3.png` | 3 personnes bras dessus bras dessous | équipe, label, collectif, la communauté, « on est ensemble » |
| `icons/entraide-coup-de-main.png` | une personne sur une marche qui tire l'autre vers le haut | manager / promoteur / éditeur qui fait monter un artiste, ouvrir des portes |
| `icons/porter-un-frere.png` | une personne qui en porte une autre sur son dos | porter un artiste, soutien, « il l'a porté », grand frère du game |

## Extraits classés par pilier (`extraits/`)

| Fichier | Pilier | Contenu |
|---|---|---|
| `extraits/musique/tv-big-up-monsieur-vass.mp4` | MUSIQUE | Émission TV (repost TikTok, image 16:9 au centre, y 318–642) : collab avec Z de 13 Block, « un gros big up à Monsieur Vass, c'est un influenceur TikTok » à 13,5 s |
| `extraits/musique/sortie-concert-nuit.mp4` | MUSIQUE | Sortie de concert de nuit avec les artistes, photo de groupe à 9 s |
| `extraits/musique/dopelym-live-afrique.mp4` | MUSIQUE | Dopelym en live en Afrique (foule, fumigènes), 0–20 s ; filigrane TikTok : recadrer 15 % de chaque côté |
| `extraits/musique/dopelym-clip-voiture.mp4` | MUSIQUE | Extrait de clip de Dopelym (voitures, lui dans la voiture), 0–22 s |
| `extraits/musique/kadja-freestyle-kordial-3.mp4` | MUSIQUE | Teaser carré 576×576 du clip « Freestyle Kordial 3 » de Kadja, titre à 11–13,5 s ; filigrane @kadjaofficiel en haut à gauche puis en bas à droite (flouter + créditer) |
| `extraits/musique/philipayne-thb-deux-mondes.mov` | MUSIQUE | Teaser vertical 720×1280 de « Deux Mondes » (Philipayne × THB), titre à 5–7 s, « disponible mercredi 18h » à 15 s ; pas de filigrane |
| `extraits/musique/burna-boy-nfl-paris-halftime.mp4` | MUSIQUE | Burna Boy, mi-temps du match NFL à Paris, vertical 720×1280, 61 s, sans filigrane ; sur le terrain 22–30 s |
| `extraits/musique/burna-boy-gbona-live.mp4` | MUSIQUE | « Gbona », live YouTube Music Nights, vertical 1080×1920, 60 s ; scène 12–16 s, flammes 40–48 s |
| `extraits/musique/jeune-lion-wtfgo-1.mov`, `jeune-lion-wtfgo-2.mp4` | MUSIQUE | Teasers « WTFGO » de Jeune Lion (dragons, feu, Paris en ruines), 576×1024 ; filigrane @jeunelion13 à flouter (milieu gauche puis bas droite) + crédit |
| `extraits/musique/didib-stade-fhb-concert-16x9.mp4` | MUSIQUE | Didi B au stade FHB (Félicia), 3 mai 2025 : plaques de platine sur scène, foule ; TikTok vertical recadré 16:9 (fond flouté), filigrane flouté (source TikTok @marcel.media0), 1 min 39 avec son |
| `extraits/musique/didib-je-mappelle-clip-16x9.mp4` | MUSIQUE | coulisses du clip « Je m'appelle » (Didi B feat. Zlatan), « OUT NOW » ; TikTok vertical recadré 16:9, filigranes et lien YouTube floutés (source @didib.mojaveli), 21 s avec son |
| `extraits/musique/kiff-no-beat-clip-16x9.mp4` | MUSIQUE | ancien clip de Kiff No Beat (quartier, danse) ; bande vidéo extraite du TikTok et mise en 1920×1080, logos floutés (source TikTok @2x_ramazanny), 56 s avec son |
| `extraits/musique/didib-interview-planete-rap-16x9.mp4` | MUSIQUE | Didi B à Planète Rap (Skyrock), 33 s : « je suis un big par mon talent », « il y a quelques années on ne pouvait même pas parler de Zénith » (≈4–13 s), Fally Ipupa et le Stade de France (≈14–20 s) ; inserts affiche Zénith 19.04.2026 (13–16 s), vue aérienne d'Abidjan (25–29 s) ; logos Planète Rap / Skyrock floutés, créditer « PLANÈTE RAP / SKYROCK » |
| `extraits/musique/zrai-studio-16x9.mp4` | MUSIQUE | Zrai en studio (titre « ZRAI, artiste interprète » 0–3 s), session d'enregistrement, 30 s, pas de parole |
| `extraits/musique/young-jonn-diner-raba-16x9.mp4` | MUSIQUE | Dîner avec Young Jonn (titre à l'écran 9–12 s), on entend « Raba » vers 15–18 s, 18 s |
| `extraits/musique/himra-zenith-live-16x9.mp4` | MUSIQUE | Himra en live au Zénith de Paris (28 janvier 2026), gilet pare-balles, écran « 1X » ; vertical recadré 16:9 (fond flouté), pas de filigrane, 62 s avec son |
| `extraits/musique/himra-flammes-16x9.mp4` | MUSIQUE | Himra reçoit sa Flamme (musique africaine ou d'inspiration africaine) : « c'est la première flamme de l'Afrique… première flamme africaine pour la Côte d'Ivoire » (≈2–14 s), Tiakola sur scène (14–16 s) ; filigrane TikTok @lesflammesawards flouté, créditer, 21,5 s avec son |
| `extraits/musique/himra-bara-bara-teaser-16x9.mp4` | MUSIQUE | Teaser « BARA BARA » (Rolls-Royce, jet privé), carton « BARA BARA » 16,8–19,4 s puis « 15.05 » ; TikTok @machettehimra flouté, fin TikTok coupée, 21 s avec son |
| `extraits/musique/himra-clip-sorry-im-bad-16x9.mp4` | MUSIQUE | Extrait de clip de l'album *Sorry I'm Bad* (Rolls, jet, Paris), « MAINTENANT DISPONIBLE » à 23,3 s ; TikTok @machettehimra flouté, 24 s avec son |
| `extraits/musique/himra-epic-records-promo-16x9.mp4` | MUSIQUE | Vidéo promo de la signature chez Epic Records France : Abidjan, appel « Epic Records » (≈35 s), bureaux Epic et disques d'or, carton final « HIMRA – Sorry I'm Bad – 29.05.26 – Epic / Sony Music » (45–53 s) ; pas de filigrane |
| `extraits/musique/burna-boy-grammys-2024-brandy-16x9.mp4` | MUSIQUE | Burna Boy sur la scène des Grammys (4 février 2024) avec Brandy (« Sittin' On Top of the World »), 27,6 s ; logo Grammy flouté, créditer « SOURCE : GRAMMYS / RECORDING ACADEMY » |
| `extraits/culture/tapis-rouge-evenement.mp4` | CULTURE | Tapis rouge d'un événement, sans parole |
| `extraits/culture/interview-monsieur-vass.mp4` | CULTURE | Son interview (image 16:9 au centre) : « je vais continuer à faire du contenu » (0–3,3 s), vidéos réactions, New Wave |
| `extraits/sport/yan-diomande-but-montage.mov` | SPORT | Montage du but de Yan Diomandé (Real Madrid, n°25) : frappe 0,6–4 s, célébration 6 s, gros plans 19–22 s ; filigrane TikTok : recadrer à 78 % |
| `extraits/sport/yan-diomande-but-tribune.mp4` | SPORT | Le même match filmé en tribune, célébration 14–18 s |
| `extraits/sport/cote-divoire-coupe-du-monde.mp4` | SPORT | Sa vidéo Côte d'Ivoire / Coupe du monde : Infantino, Éléphants, poule avec l'Allemagne, « restez concentrés » à 36,9 s |

Logo : `showreel/assets/logos/monsieur-vass.png`.
