// Adaptateur de lecture seul : configuration compilée, sans compte, binding ni accès réseau.
import catalogue from '../../catalogue/catalogue.json' with {type:'json'};
import questions from '../../form/questions.json' with {type:'json'};
import guide from '../../capture-guide/ecrans.json' with {type:'json'};
import partition from '../../montage/partition.json' with {type:'json'};
import audio from '../../audio/profil.json' with {type:'json'};
const entree=catalogue.entries[0];
export default {async fetch(req){const url=new URL(req.url);if(req.method!=='GET')return new Response('Méthode non permise',{status:405,headers:{Allow:'GET'}});if(url.pathname==='/v1/catalogue')return Response.json(catalogue);if(url.pathname==='/v1/health')return Response.json({mode:'reference',renderer:'github-actions',ota_implemented:false});if(url.pathname===`/v1/templates/${entree.template_id}/${entree.version}`)return Response.json({entree,questions,ecrans:guide,partition,audio});return new Response('Introuvable',{status:404})}};
