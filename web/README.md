# Front de la salle de marché (React, Vite, Tailwind)

Prérequis : Node 20 ou plus récent.

```bash
cd web
npm install
npm run dev        # http://localhost:5173, l'API doit tourner sur http://localhost:8000
npm run build      # produit web/dist, servi automatiquement par l'API (uvicorn api.main:app)
```

Structure :

```
src/main.tsx          routes : /  (hall), /room/:code (salle de marché du trader), /desk/:code (poste du formateur)
src/api.ts            client typé de l'API et stockage du jeton par salle
src/i18n.ts           textes FR / EN
src/styles.css        jetons du système de design (palette neutre, un accent, deux poids)
src/components/ui.tsx Button, Field, Badge, Stat, Section, TopBar, Bars
src/pages/            Hall, Room, Desk
```
