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
  hero_1: ['Chaque participant représente un pays du West African Power Pool, dépose ses offres pour le lendemain et observe le clearing.', 'Each participant represents a West African Power Pool country, submits orders for the next day and watches the clearing.'],
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
