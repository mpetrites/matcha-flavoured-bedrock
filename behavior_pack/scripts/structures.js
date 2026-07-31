import { system, world } from "@minecraft/server";

const SPACING=1280, OFFSET_RANGE=480, SALT=10387312, MARKER="matcha_beta_village_marker";
const ALLOWED_BIOMES=new Set(["minecraft:plains","minecraft:sunflower_plains","minecraft:desert","minecraft:savanna","minecraft:snowy_plains","minecraft:taiga","minecraft:old_growth_pine_taiga","minecraft:old_growth_spruce_taiga"]);
// Expanded arrays preserve the weights from the pinned Java template pools.
const BUILDINGS=["small_1","medium_1","medium_1","medium_2","medium_2","medium_2","large_1","large_1","extra_large_1","extra_large_1","extra_large_1","extra_large_1","extra_large_2","extra_large_2","extra_large_2","extra_large_2","extra_large_2","extra_large_3","extra_large_3","extra_large_4","extra_large_5","extra_large_5","extra_large_5","extra_large_5"];
const ROADS=["end","end","end","joint_t","joint_l","straight","straight"];
function hash(x,z,salt=SALT) { let v=(Math.imul(x,73428767)^Math.imul(z,912931)^salt)>>>0;v^=v>>>13;v=Math.imul(v,1274126177);return (v^(v>>>16))>>>0; }
function candidate(gridX,gridZ) { return {x:gridX*SPACING+(hash(gridX,gridZ)%OFFSET_RANGE),z:gridZ*SPACING+(hash(gridZ,gridX,SALT+1)%OFFSET_RANGE)}; }
function load(dimension,name,x,y,z,rotation="0_degrees") { try { dimension.runCommand(`structure load matcha:village_beta/${name} ${x} ${y} ${z} ${rotation} none false true`); } catch {} }
function buildVillage(dimension,location,seed) {
  load(dimension,"town_centers/well",location.x,location.y,location.z);
  load(dimension,`roads/${ROADS[seed%ROADS.length]}`,location.x-5,location.y,location.z+8,"90_degrees");
  load(dimension,`roads/${ROADS[(seed+3)%ROADS.length]}`,location.x+8,location.y,location.z-5,"0_degrees");
  const layouts=[[-24,0,"90_degrees"],[24,0,"270_degrees"],[0,-24,"180_degrees"],[0,24,"0_degrees"],[-22,-22,"180_degrees"],[22,22,"0_degrees"]];
  layouts.forEach(([dx,dz,rotation],index)=>load(dimension,`buildings/${BUILDINGS[(seed+index*7)%BUILDINGS.length]}`,location.x+dx,location.y,location.z+dz,rotation));
  const marker=dimension.spawnEntity("minecraft:armor_stand",{x:location.x+0.5,y:location.y,z:location.z+0.5});marker.addTag(MARKER);marker.addEffect("invisibility",20000000,{showParticles:false});marker.nameTag="";
  for (let i=0;i<4;i++) try { dimension.spawnEntity("minecraft:villager_v2",{x:location.x-4+i*3,y:location.y+1,z:location.z+3}); } catch {}
}
function tryGenerate(player) {
  if (player.dimension.id!=="minecraft:overworld")return;const gridX=Math.floor(player.location.x/SPACING),gridZ=Math.floor(player.location.z/SPACING);
  for (let gx=gridX-1;gx<=gridX+1;gx++)for(let gz=gridZ-1;gz<=gridZ+1;gz++){
    const site=candidate(gx,gz),dx=player.location.x-site.x,dz=player.location.z-site.z;if(dx*dx+dz*dz>128*128)continue;
    let top,biome;try{top=player.dimension.getTopmostBlock({x:site.x,z:site.z});biome=player.dimension.getBiome({x:site.x,y:top.location.y,z:site.z})?.id;}catch{continue;}
    // Anchor the duplicate check to the surface, not the player's Y. A player
    // approaching through a deep cave could otherwise generate the same site
    // a second time because its existing marker was outside the 3D radius.
    if(player.dimension.getEntities({type:"minecraft:armor_stand",tags:[MARKER],location:{x:site.x,y:top.location.y+1,z:site.z},maxDistance:96}).length)continue;
    if(!top||!ALLOWED_BIOMES.has(biome))continue;buildVillage(player.dimension,{x:site.x,y:top.location.y+1,z:site.z},hash(gx,gz));
  }
}
system.runInterval(()=>{for(const player of world.getAllPlayers())tryGenerate(player);},100);
