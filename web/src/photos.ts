/** Photos of the public website, with their credits. All come from Wikimedia Commons under the licence named
 *  here: credit them with author, licence and source (printed on each photo and listed in the footer), and keep
 *  this list in step with NOTICE. Files live in web/public/photos/ (JPEG, 1920 px wide). */
export type Photo = { src: string; en: string; fr: string; creator: string; license: string; licenseUrl: string; source: string; /** CSS object-position: the part of the photo kept when it is cropped */ position?: string }

export const PHOTOS = {
  'akosombo-dam': { src: '/photos/akosombo-dam.jpg', en: 'Spillway of the Akosombo dam, Ghana', fr: 'Évacuateur du barrage d’Akosombo, Ghana', creator: 'ZSM', license: 'CC BY-SA 3.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0/', source: 'https://commons.wikimedia.org/w/index.php?curid=11989962', position: 'center 55%' },
  'solar-technicians': { src: '/photos/solar-technicians.jpg', en: 'Technicians carrying a solar panel (Innovation: Africa)', fr: 'Techniciens portant un panneau solaire (Innovation: Africa)', creator: 'IAfrica76', license: 'CC0 1.0', licenseUrl: 'https://creativecommons.org/publicdomain/zero/1.0/', source: 'https://commons.wikimedia.org/w/index.php?curid=163952895', position: 'center 35%' },
  'rural-electrification-nigeria': { src: '/photos/rural-electrification-nigeria.jpg', en: 'Rural electrification, Chori village, Nigeria', fr: 'Électrification rurale, village de Chori, Nigeria', creator: 'Kambai Akau', license: 'CC BY-SA 4.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/', source: 'https://commons.wikimedia.org/w/index.php?curid=119450281', position: 'center 40%' },
} satisfies Record<string, Photo>

export type PhotoId = keyof typeof PHOTOS

export const photoAlt = (id: PhotoId, lang: string) => (lang === 'fr' ? PHOTOS[id].fr : PHOTOS[id].en)
/** "Photo : ZSM, CC BY-SA 3.0" (the credit line printed on the photo). */
export const photoCredit = (id: PhotoId, lang: string) => `${lang === 'fr' ? 'Photo :' : 'Photo:'} ${PHOTOS[id].creator}, ${PHOTOS[id].license}`
