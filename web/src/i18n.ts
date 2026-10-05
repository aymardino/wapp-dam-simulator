import { createContext, createElement, useContext, useState, type ReactNode } from 'react'

export type Lang = 'fr' | 'en'
const STR: Record<string, [string, string]> = {
  app_title: ['Simulateur de marché day-ahead du WAPP', 'WAPP day-ahead market simulator'],
  app_tagline: ['Implémentation ouverte de référence du couplage de marché zonal', 'Open reference implementation of zonal market coupling'],
  create_room: ['Créer une salle', 'Create a room'], join_room: ['Rejoindre une salle', 'Join a room'],
  room_name: ['Nom de la salle', 'Room name'], trainer_name: ['Nom du formateur', 'Trainer name'],
  room_code: ['Code de la salle', 'Room code'], your_name: ['Votre organisation', 'Your organisation'],
  zone: ['Zone', 'Zone'], role: ['Rôle', 'Role'], trader: ['Trader', 'Trader'], observer: ['Observateur', 'Observer'],
  create: ['Créer', 'Create'], join: ['Rejoindre', 'Join'], save: ['Enregistrer', 'Save'], add: ['Ajouter', 'Add'],
  remove: ['Retirer', 'Remove'], cancel: ['Annuler', 'Cancel'], reset: ['Réinitialiser', 'Reset'],
  phase_submission: ['Soumission ouverte', 'Submission open'], phase_cleared: ['Marché clôturé', 'Market cleared'],
  delivery: ['Livraison', 'Delivery'], hours24: ['24 h', '24 h'], hour: ['Heure', 'Hour'],
  my_orders: ['Mon carnet d’ordres', 'My order book'], supply: ['Vente', 'Sell'], demand: ['Achat', 'Buy'],
  blocks: ['Blocs', 'Blocks'], mic: ['Conditions de revenu minimum', 'Minimum income conditions'],
  actor: ['Actif', 'Asset'], mw: ['MW', 'MW'], price: ['Prix', 'Price'], profile: ['Profil', 'Profile'],
  segment: ['Seg.', 'Seg.'], side: ['Sens', 'Side'], start: ['Début', 'Start'], end: ['Fin', 'End'],
  parent: ['Parent', 'Parent'], group: ['Groupe', 'Group'], fixed: ['Terme fixe', 'Fixed term'], variable: ['Terme variable', 'Variable term'],
  market: ['Marché', 'Market'], last_clearing: ['Dernier clearing', 'Last clearing'], no_clearing: ['Aucun clearing pour l’instant.', 'No clearing yet.'],
  zone_prices: ['Prix par zone', 'Zonal prices'], avg24: ['Moy.', 'Avg.'], position: ['Position', 'Position'],
  my_result: ['Mon résultat', 'My result'], sold: ['Vendu', 'Sold'], bought: ['Acheté', 'Bought'], surplus: ['Surplus', 'Surplus'],
  rejected: ['Rejeté', 'Rejected'], accepted: ['Accepté', 'Accepted'], offered: ['Offert', 'Offered'], avg_price: ['Prix moyen', 'Avg price'],
  status: ['Statut', 'Status'], saved: ['Enregistré', 'Saved'], closed_hint: ['La soumission est clôturée.', 'Submission is closed.'],
  desk: ['Poste du formateur', 'Trainer desk'], participants: ['Participants', 'Participants'], orders: ['Ordres', 'Orders'],
  settings: ['Paramètres', 'Settings'], rules: ['Règles', 'Rules'], pricing: ['Règle de prix', 'Pricing rule'],
  pab: ['Blocs paradoxaux', 'Paradoxical blocks'], tie: ['Partage des ex æquo', 'Equal-price sharing'],
  fill_missing: ['Compléter les zones sans soumission', 'Fill zones without submission'], currency: ['Monnaie', 'Currency'],
  horizon: ['Horizon', 'Horizon'], one_hour: ['Une heure', 'One hour'], ntc: ['Capacités (NTC)', 'Capacities (NTC)'],
  line: ['Ligne', 'Line'], default: ['Défaut', 'Default'], current: ['Actuelle', 'Current'],
  run_clearing: ['Lancer le clearing', 'Run clearing'], running: ['Calcul en cours…', 'Running…'],
  open_market: ['Rouvrir la soumission', 'Reopen submission'], close_market: ['Clôturer la soumission', 'Close submission'],
  welfare: ['Welfare', 'Welfare'], volume: ['Volume', 'Volume'], checks: ['Vérifications', 'Checks'],
  check_pro: ['Ordres paradoxalement rejetés', 'Paradoxically rejected orders'], check_gaps: ['Écarts de prix sans congestion', 'Price gaps without congestion'],
  check_tie: ['Départage', 'Tie-break'], copy_code: ['Code à partager aux participants', 'Code to share with participants'],
  error: ['Erreur', 'Error'], no_orders: ['Aucun ordre déposé dans cette salle.', 'No order submitted in this room.'],
  withdrawn: ['retirée (MIC)', 'withdrawn (MIC)'], hours_label: ['Heures simulées', 'Simulated hours'],
  trader_count: ['traders', 'traders'], back: ['Accueil', 'Home'],
  my_rooms: ['Vos salles', 'Your rooms'], as_trainer: ['Poste du formateur', 'Trainer desk'], as_member: ['Salle de marché', 'Trading floor'],
  forget: ['Oublier', 'Forget'], switch_desk: ['Passer au poste du formateur', 'Switch to the trainer desk'], switch_room: ['Entrer dans la salle comme trader', 'Enter the floor as a trader'],
  hero_1: ['Chaque participant représente un acteur du marché dans un pays du West African Power Pool : société d\u2019électricité, producteur ou distributeur. Il dépose ses offres pour le lendemain et observe le clearing. Plusieurs acteurs peuvent partager un pays.', 'Each participant represents a market actor in a West African Power Pool country: a utility, a producer or a distributor. They submit orders for the next day and watch the clearing. Several actors can share a country.'],
  empty_supply: ['Aucune offre de vente. Ajoutez un segment prix / quantité par centrale.', 'No sell order yet. Add a price / quantity segment per plant.'],
  empty_demand: ['Aucune offre d\u2019achat. Ajoutez la demande de votre réseau par segment.', 'No buy order yet. Add your grid demand by segment.'],
  empty_blocks: ['Aucun bloc. Un bloc est accepté en totalité sur sa plage horaire, ou rejeté.', 'No block. A block is fully accepted over its hours, or rejected.'],
  empty_mic: ['Aucune condition. Une condition retire vos offres si la recette est insuffisante.', 'No condition. A condition withdraws your orders if revenue falls short.'],
  waiting_clearing: ['En attente du clearing lancé par le formateur.', 'Waiting for the trainer to run the clearing.'],
  network: ['Réseau', 'Network'], prices_at: ['Prix à', 'Prices at'], saved_at: ['Enregistré à', 'Saved at'],
  run_hint: ['Exécute le moteur avec les ordres déposés ; les zones sans soumission sont complétées si l\u2019option est cochée.', 'Runs the engine with submitted orders; zones without submission are filled when the option is checked.'],
  results: ['Résultats', 'Results'], invite: ['Partagez ce code aux participants', 'Share this code with participants'],
  reference_badge: ['Données de référence', 'Reference data'], zones_word: ['zone(s)', 'zone(s)'],
  demo_badge: ['Démonstration : aucune offre de participant, les 14 zones viennent des données de référence', 'Demonstration: no participant order, all 14 zones come from reference data'],
  with_orders: ['zone(s) avec ordres', 'zone(s) with orders'], without_orders: ['sans soumission', 'without submission'],
  will_fill: ['complétée(s) par les données de référence', 'filled with reference data'], will_ignore: ['ignorée(s)', 'ignored'],
  scenario: ['Scénario', 'Scenario'], tab_map: ['Carte', 'Map'], tab_prices: ['Prix', 'Prices'], tab_dispatch: ['Dispatch', 'Dispatch'], tab_flows: ['Flux', 'Flows'],
  export_json: ['Résultats (JSON)', 'Results (JSON)'], export_csv: ['Prix (CSV)', 'Prices (CSV)'], live: ['En direct', 'Live'],
  p_solar: ['Solaire', 'Solar'], p_hydro: ['Hydraulique', 'Hydro'], p_baseload: ['Base thermique', 'Thermal baseload'], p_flat: ['Constant', 'Flat'], p_custom: ['Autre', 'Other'], p_peaker: ['Pointe', 'Peaking'], p_block: ['Blocs', 'Blocks'], p_demand: ['Demande acceptée', 'Accepted demand'],
  name_hint: ['Nom affiché aux autres participants, unique dans la salle', 'Name shown to other participants, unique in the room'],
  guide_trainer: ['Guide du formateur', 'Trainer guide'], guide_trader: ['Guide du trader', 'Trader guide'], guides: ['Guides', 'Guides'],
  fill_mode: ['Complétion', 'Fill mode'], fill_actors: ['Acteurs de fond (recommandé)', 'Background actors (recommended)'],
  fill_zones: ['Zones sans soumission', 'Zones without submission'], fill_none: ['Aucune', 'None'],
  fill_actors_hint: ['Tous les acteurs du scénario restent, sauf ceux qu\u2019un participant remplace par son nom ou ses ordres.', 'All scenario actors stay, except those a participant replaces by name or by orders.'],
  fill_zones_hint: ['Une zone avec au moins un ordre ne contient que les ordres des participants ; les autres sont complétées.', 'A zone with at least one order contains only participants\u2019 orders; the others are filled.'],
  fill_none_hint: ['Seuls les ordres des participants comptent.', 'Only participants\u2019 orders count.'],
  about: ['À propos', 'About'],
  tour_skip: ['Passer', 'Skip'], tour_next: ['Suivant', 'Next'], tour_done: ['Compris', 'Got it'], tour_replay: ['Visite guidée', 'Guided tour'],
  tour_hall_1_t: ['Vous animez la séance ?', 'Running the session?'], tour_hall_1_x: ['Créez une salle : vous recevez un code à partager avec les participants.', 'Create a room: you get a code to share with the participants.'],
  tour_hall_2_t: ['Vous participez ?', 'Taking part?'], tour_hall_2_x: ['Entrez le code reçu, le nom de votre organisation et votre pays.', 'Enter the code you received, your organisation and your country.'],
  tour_desk_1_t: ['Le code de la salle', 'The room code'], tour_desk_1_x: ['Partagez-le : c’est tout ce qu’il faut aux participants pour entrer.', 'Share it: that is all participants need to get in.'],
  tour_desk_2_t: ['Le scénario et les règles', 'Scenario and rules'], tour_desk_2_x: ['Choisissez les données de fond et les heures simulées. Tout s’enregistre tout seul.', 'Pick the background data and the simulated hours. Everything saves by itself.'],
  tour_desk_3_t: ['Lancez le calcul', 'Run the clearing'], tour_desk_3_x: ['Quand les offres sont déposées, lancez le clearing : les prix et les flux s’affichent pour tout le monde.', 'Once orders are in, run the clearing: prices and flows show up for everyone.'],
  tour_room_1_t: ['Votre carnet d’ordres', 'Your order book'], tour_room_1_x: ['Ajoutez vos offres de vente et d’achat : une quantité en MW, un prix. Puis enregistrez.', 'Add your sell and buy orders: a quantity in MW, a price. Then save.'],
  tour_room_2_t: ['Le marché', 'The market'], tour_room_2_x: ['Après le calcul lancé par le formateur, la carte et les prix de tous les pays apparaissent ici.', 'After the trainer runs the clearing, the map and every country’s price appear here.'],
  tour_room_3_t: ['Votre résultat', 'Your result'], tour_room_3_x: ['Ce que vous avez vendu ou acheté, à quel prix, et ce qui a été refusé.', 'What you sold or bought, at what price, and what was rejected.'],
  autosave: ['Enregistré automatiquement', 'Saved automatically'],
  order_book_hint: ['Vos ordres sont remplacés à chaque enregistrement.', 'Your orders are replaced on each save.'],
}

const Ctx = createContext<{ lang: Lang; setLang: (l: Lang) => void }>({ lang: 'fr', setLang: () => {} })

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => (localStorage.getItem('wapp:lang') as Lang) || 'fr')
  const setLang = (l: Lang) => { localStorage.setItem('wapp:lang', l); setLangState(l) }
  return createElement(Ctx.Provider, { value: { lang, setLang } }, children)
}

export function useLang() { return useContext(Ctx) }

export function useT() {
  const { lang } = useContext(Ctx)
  return (key: string) => { const pair = STR[key]; return pair ? (lang === 'fr' ? pair[0] : pair[1]) : key }
}
