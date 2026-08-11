/* =========================================================================
   İT Tədris Laboratoriyası — interaktiv 3D dizayner
   Three.js r128 (UMD) + OrbitControls
   ========================================================================= */
'use strict';

/* ---------------------------------------------------------------- KATALOQ */
/* w,d — mebelin döşəmə ölçüsü (m)
   cx,cz — tələb olunan boş məsafə: yalnız oturacaq olan tərəfdə böyükdür.
           Podda stullar ±z tərəfdədir, ona görə cz=0,45 (iki pod arasında 0,9 m),
           yan-yana duran podlar üçün isə 0,05 kifayətdir.
   seats — tələbə iş yeri sayı;  price — AZN (layihə sənədindəki qiymətlər)      */
const CATALOG = {
  pod:      {nm:'Pod — 4 iş yeri',       w:1.85, d:1.10, cx:0.05, cz:0.45, seats:4, price:7710, col:0x3498db},
  desk1:    {nm:'Tək iş yeri',           w:1.20, d:0.60, cx:0.05, cz:0.45, seats:1, price:1940, col:0x5dade2},
  // cz yalnız yanaşma zolağıdır; Ø1,5 m manevr dairəsi ayrıca yoxlanılır
  a11y:     {nm:'Əlçatan iş yeri ♿',    w:1.40, d:0.75, cx:0.35, cz:0.55, seats:1, price:2640, col:0x2980b9, a11y:true},
  teacher:  {nm:'Müəllim stansiyası',    w:1.85, d:0.78, cx:0.05, cz:0.45, seats:0, price:3350, col:0xe67e22},
  byod:     {nm:'BYOD masası — 6 yer',   w:1.45, d:1.75, cx:0.50, cz:0.50, seats:6, price:1400, col:0xc0392b},
  iot:      {nm:'IoT skamyası — 6 yer',  w:3.15, d:0.58, cx:0.05, cz:0.50, seats:6, price:3800, col:0x16a085},
  gpu:      {nm:'AI / GPU stansiyası',   w:1.20, d:0.70, cx:0.05, cz:0.45, seats:0, price:6200, col:0x9b59b6},
  rack:     {nm:'Server rack 19"',       w:0.82, d:0.75, cx:0.05, cz:0.05, seats:0, price:12300, col:0x8e44ad, h:2.00, equip:true},
  ups:      {nm:'UPS',                   w:0.78, d:0.75, cx:0.05, cz:0.05, seats:0, price:2800, col:0x7d3c98, h:1.15, equip:true},
  nas:      {nm:'NAS — yedəkləmə',       w:0.50, d:0.50, cx:0.05, cz:0.05, seats:0, price:3400, col:0xa569bd, h:0.45, equip:true},
  printer:  {nm:'3D printer + MFP',      w:1.35, d:0.58, cx:0.05, cz:0.40, seats:0, price:2200, col:0x7f8c8d, equip:true},
  cabinet:  {nm:'Şkaf',                  w:0.90, d:0.50, cx:0.05, cz:0.30, seats:0, price:900,  col:0x95a5a6, h:1.80, equip:true},
  panel:    {nm:'İnteraktiv panel 86"',  w:2.00, d:0.12, cx:0, cz:0, seats:0, price:5200, col:0x2c3e50, wall:true, my:1.05, h:1.15},
  screen55: {nm:'Komanda ekranı 55"',    w:1.25, d:0.10, cx:0, cz:0, seats:0, price:1100, col:0x2c3e50, wall:true, my:1.30, h:0.72},
  ac:       {nm:'Kondisioner',           w:1.00, d:0.26, cx:0, cz:0, seats:0, price:1400, col:0x85c1e9, wall:true, my:2.25, h:0.32}
};

/* İlkin plan — 12,5 × 7,5 m (93,8 m²).
   Ölçü analizdən çıxarılıb: 24 sabit + 12 çevik + 2 əlçatan yer üçün
   tələb olunan minimum 81,4 m²-dir; qalan 12,4 m² sıralar arasında 1,40 m
   keçid yolunu və manevr dairələrini təmin edir.
   Otaq ölçüsü sol paneldən dəyişdirilə bilər. */
const DEFAULT_ROOM = {W:12.5, D:7.5, H:2.8};
const DEFAULT_LAYOUT = [
  {t:'pod', x:1.53, z:5.30}, {t:'pod', x:3.93, z:5.30}, {t:'pod', x:6.33, z:5.30},
  {t:'pod', x:1.53, z:2.80}, {t:'pod', x:3.93, z:2.80}, {t:'pod', x:6.33, z:2.80},
  {t:'a11y',     x:8.40, z:5.20}, {t:'a11y', x:8.40, z:2.80},
  {t:'teacher',  x:9.90, z:7.05},
  {t:'rack',     x:0.72, z:6.90}, {t:'ups', x:1.58, z:6.90}, {t:'nas', x:2.38, z:6.90},
  {t:'byod',     x:11.00, z:4.00},
  {t:'gpu',      x:11.60, z:1.60, r:-90},
  {t:'iot',      x:1.90, z:0.58},
  {t:'printer',  x:4.95, z:0.58},
  {t:'cabinet',  x:12.22, z:6.60, r:90},
  {t:'panel',    x:5.00, z:7.50, r:180},
  // Komanda ekranı BYOD masasının (z≈4,0) qarşısındadır; əvvəlki z=5,60
  // mövqeyində 1,80 m-lik şkafla toqquşurdu — şaquli yoxlama bunu aşkarladı.
  {t:'screen55', x:12.5, z:4.60, r:-90},
  {t:'ac',       x:0.00, z:3.60, r:90}, {t:'ac', x:12.5, z:6.60, r:-90}
];

/* ------------------------------------------------------------------ VƏZİYYƏT */
const S = {
  W:10, D:7, H:2.8,
  objects:  [],          // {id,type,x,z,rot,group,zone,def}
  selected: null,
  snap:     0.1,
  showWalls:true,
  showZones:true,
  mode:     '3d',
  undo:     [],
  nextId:   1
};

/* ------------------------------------------------------------------ SƏHNƏ */
const view = document.getElementById('view');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b1118);
scene.fog = new THREE.Fog(0x0b1118, 26, 60);

const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 200);
camera.position.set(13.5, 11, 15.5);

/* WebGL olmayan/bloklanmış brauzerdə tətbiq "yüklənir…" ekranında donmamalıdır —
   səbəb istifadəçiyə açıq şəkildə bildirilir. */
function fatal(msg){
  const ld = document.getElementById('loading');
  if(ld) ld.innerHTML =
    '<div style="font-size:15px;font-weight:700;color:#e74c3c">Tətbiq işə düşmədi</div>' +
    '<div style="font-size:12px;color:#94a5b8;max-width:420px;text-align:center;line-height:1.6">' +
    msg + '</div>';
  throw new Error(msg);
}

let renderer;
try{
  renderer = new THREE.WebGLRenderer({antialias:true, preserveDrawingBuffer:true});
}catch(e){
  fatal('Brauzer WebGL dəstəkləmir və ya qrafik sürətləndirmə söndürülüb. ' +
        'Brauzer parametrlərində aparat sürətləndirməsini aktivləşdirin.');
}
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputEncoding = THREE.sRGBEncoding;          // düzgün rəng fəzası
renderer.toneMapping = THREE.ACESFilmicToneMapping;    // kinematik ton əyrisi
renderer.toneMappingExposure = 0.92;
view.appendChild(renderer.domElement);

/* Təkrar istifadə olunan (keşlənmiş) geometriya, material və teksturalar.
   Səhnə yenidən qurulanda yalnız bu dəstdə OLMAYAN resurslar dispose edilir —
   paylaşılan resursu azad etmək digər obyektləri sındırardı.
   WeakSet seçilib, çünki clone() userData-nı da köçürür və nişan yayılardı. */
const SHARED = new WeakSet();
function keep(x){ SHARED.add(x); return x; }

/* Səhnədən çıxarılan qolun bütün fərdi resurslarını azad edir */
function disposeTree(root){
  root.traverse(o=>{
    if(o.geometry && !SHARED.has(o.geometry)) o.geometry.dispose();
    const mats = !o.material ? [] : (Array.isArray(o.material) ? o.material : [o.material]);
    mats.forEach(m=>{
      if(!m || SHARED.has(m)) return;
      ['map','normalMap','aoMap','roughnessMap','metalnessMap','emissiveMap','alphaMap']
        .forEach(k=>{ if(m[k] && !SHARED.has(m[k])) m[k].dispose(); });
      m.dispose();
    });
  });
}
function clearGroup(g){
  while(g.children.length){ const c = g.children[0]; disposeTree(c); g.remove(c); }
}

/* ---------- PBR aktivləri (CC0 — Poly Haven) ----------
   Fayl file:// ilə açılarsa, brauzer CORS səbəbindən assets/ qovluğunu
   yükləmir və səhnə boz açılır. Əvvəllər bu SƏSSİZ baş verirdi — indi
   istifadəçiyə səbəb və həll yolu göstərilir. */
let assetFail = 0;
function assetError(){
  if(++assetFail !== 1) return;                 // banner bir dəfə göstərilir
  const isFile = location.protocol === 'file:';
  const b = document.createElement('div');
  b.style.cssText = 'position:fixed;left:0;right:0;top:0;z-index:9999;padding:12px 18px;'
    + 'background:#7d2320;color:#fff;font:13px/1.6 Segoe UI,sans-serif;text-align:center';
  b.innerHTML = isFile
    ? 'Səhnə natamam yükləndi: brauzer <b>file://</b> rejimində teksturaları '
      + 'bloklayır (CORS). Lokal server lazımdır — <b>BASLAT.bat</b> '
      + '(Windows) və ya <b>sh baslat.sh</b> (Linux/macOS) ilə açın.'
    : 'Bəzi teksturalar yüklənmədi — <b>assets/</b> qovluğunun yerində '
      + 'olduğunu yoxlayın.';
  document.body.appendChild(b);
}

const texLoader = new THREE.TextureLoader();
function tex(file, srgb, rx, ry){
  const t = texLoader.load('assets/' + file, undefined, undefined, assetError);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8;
  if(srgb) t.encoding = THREE.sRGBEncoding;
  if(rx) t.repeat.set(rx, ry === undefined ? rx : ry);
  return keep(t);
}
/* arm = AO(R) / Roughness(G) / Metalness(B) — bir faylda üç xəritə */
const TX = {
  floor: {d:tex('floor_diff.jpg', true), n:tex('floor_nor.jpg'), a:tex('floor_arm.jpg')},
  wall:  {d:tex('wall_diff.jpg',  true, 4), n:tex('wall_nor.jpg', false, 4), a:tex('wall_arm.jpg', false, 4)},
  desk:  {d:tex('desk_diff.jpg',  true), n:tex('desk_nor.jpg'),  a:tex('desk_arm.jpg')},
  fab:   {d:tex('fabric_diff.jpg',true, 3), n:tex('fabric_nor.jpg', false, 3), a:tex('fabric_arm.jpg', false, 3)}
};
function pbr(set, extra){
  return keep(new THREE.MeshStandardMaterial(Object.assign({
    map:set.d, normalMap:set.n,
    aoMap:set.a, roughnessMap:set.a, metalnessMap:set.a,
    roughness:1, metalness:1, envMapIntensity:1
  }, extra || {})));
}

/* Mühit işığı — real HDRI səma (pəncərələrdən düşən işıq və əkslər) */
function loadEnvironment(done){
  new THREE.RGBELoader().load('assets/sky_1k.hdr', hdr=>{
    const pmrem = new THREE.PMREMGenerator(renderer);
    pmrem.compileEquirectangularShader();
    scene.environment = pmrem.fromEquirectangular(hdr).texture;
    hdr.dispose(); pmrem.dispose();
    done();
  }, undefined, ()=>{ assetError(); done(); });   // HDRI yüklənməsə də tətbiq açılır
}

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.maxPolarAngle = Math.PI/2 - 0.03;
controls.minDistance = 3;
controls.maxDistance = 45;
controls.target.set(S.W/2, 0.8, S.D/2);

/* İşıqlar — mühit xəritəsi ambientin çoxunu verir, ona görə birbaşa işıq yumşaqdır */
scene.add(new THREE.HemisphereLight(0xeef5fc, 0x64748a, 0.22));
const sun = new THREE.DirectionalLight(0xfff4e2, 0.95);
sun.position.set(7, 19, 11);
sun.castShadow = true;
sun.shadow.radius = 3;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -16; sun.shadow.camera.right = 16;
sun.shadow.camera.top = 16;   sun.shadow.camera.bottom = -16;
sun.shadow.bias = -0.0008;
scene.add(sun);
scene.add(sun.target);
const fill = new THREE.DirectionalLight(0xcfe2f7, 0.22);   // pəncərə tərəfindən soyuq işıq
fill.position.set(-9, 6, 2);
scene.add(fill);

/* Konteynerlər */
const roomGroup  = new THREE.Group(); scene.add(roomGroup);
const objGroup   = new THREE.Group(); scene.add(objGroup);
const zoneGroup  = new THREE.Group(); scene.add(zoneGroup);

/* Seçim çərçivəsi */
const selBox = new THREE.LineSegments(
  new THREE.EdgesGeometry(new THREE.BoxGeometry(1,1,1)),
  new THREE.LineBasicMaterial({color:0xffd24a, depthTest:false})
);
selBox.renderOrder = 999;
selBox.visible = false;
scene.add(selBox);

/* ------------------------------------------------------------------ MATERİAL */
const M = {};
function mat(col, opts){
  const key = col + JSON.stringify(opts||{});
  if(!M[key]) M[key] = keep(new THREE.MeshStandardMaterial(
    Object.assign({color:col, roughness:0.72, metalness:0.05, envMapIntensity:0.38}, opts||{})));
  return M[key];
}
/* ---- prosedur teksturalar ---- */
function cnv(w, h, draw){
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.encoding = THREE.sRGBEncoding;
  t.anisotropy = 8;
  return keep(t);
}

/* monitor ekranları — üç fərqli variant */
const TEX_SCREENS = [
  cnv(320, 200, (g,w,h)=>{                     // kod redaktoru
    g.fillStyle='#151b26'; g.fillRect(0,0,w,h);
    g.fillStyle='#1d2635'; g.fillRect(0,0,w,16); g.fillRect(0,16,44,h);
    const cols=['#7fd1ff','#c3a0ff','#8ee6a8','#f0d178','#9fb0c4'];
    for(let i=0;i<15;i++){
      let x=52;
      for(let k=0;k<2+Math.random()*4;k++){
        const ww=14+Math.random()*54;
        g.fillStyle=cols[(Math.random()*cols.length)|0];
        g.globalAlpha=.85; g.fillRect(x, 26+i*11, ww, 5); g.globalAlpha=1;
        x+=ww+7; if(x>w-24) break;
      }
    }
  }),
  cnv(320, 200, (g,w,h)=>{                     // qrafik / analitika
    g.fillStyle='#f4f7fa'; g.fillRect(0,0,w,h);
    g.fillStyle='#2c3e50'; g.fillRect(0,0,w,18);
    g.strokeStyle='#dfe6ec'; g.lineWidth=1;
    for(let i=1;i<5;i++){g.beginPath();g.moveTo(20,30+i*30);g.lineTo(w-16,30+i*30);g.stroke();}
    const bc=['#3498db','#2ecc71','#e67e22','#9b59b6','#e74c3c','#1abc9c'];
    for(let i=0;i<6;i++){
      const bh=24+Math.random()*100;
      g.fillStyle=bc[i]; g.fillRect(34+i*44, 160-bh, 26, bh);
    }
  }),
  cnv(320, 200, (g,w,h)=>{                     // terminal
    g.fillStyle='#0d1117'; g.fillRect(0,0,w,h);
    g.font='11px monospace';
    for(let i=0;i<16;i++){
      g.fillStyle = i%4===0 ? '#57d97a' : '#b8c4d0';
      g.fillText((i%4===0?'$ ':'  ')+'█'.repeat(3+Math.random()*26|0), 12, 20+i*11);
    }
  })
];

/* klaviatura */
const TEX_KEYS = cnv(256, 96, (g,w,h)=>{
  g.fillStyle='#20262e'; g.fillRect(0,0,w,h);
  for(let r=0;r<5;r++) for(let c=0;c<18;c++){
    g.fillStyle='#333b45';
    g.fillRect(6+c*13.6, 6+r*17, 11.5, 14);
  }
});

const MAT_DARK   = mat(0x2b323c, {roughness:0.62});
const MAT_METAL  = mat(0xa8b0b8, {roughness:0.32, metalness:0.72});
const MAT_PLASTIC= mat(0x39404a, {roughness:0.55});
const MAT_SCREEN = mat(0x0d1117, {roughness:0.18, metalness:0.0});
const MAT_WOOD   = pbr(TX.desk, {color:0xd8cbb8});
const MAT_EDGE   = mat(0x9d8a70, {roughness:0.62});
const MAT_CHAIR  = pbr(TX.fab,  {color:0x5b6b80});
const MAT_MESH   = pbr(TX.fab,  {color:0x394454});

const GEO = {};
function bg(w,h,d){ const k=`b${w},${h},${d}`; return GEO[k] || (GEO[k] = keep(new THREE.BoxGeometry(w,h,d))); }
function cg(r,h,s){ const k=`c${r},${h},${s}`; return GEO[k] || (GEO[k] = keep(new THREE.CylinderGeometry(r,r,h,s))); }

function box(w,h,d,m,x,y,z,ry){
  const me = new THREE.Mesh(bg(w,h,d), m);
  me.position.set(x||0, y||0, z||0);
  if(ry) me.rotation.y = ry;
  me.castShadow = true; me.receiveShadow = true;
  return me;
}
function cyl(r,h,m,x,y,z,seg){
  const me = new THREE.Mesh(cg(r,h,seg||20), m);
  me.position.set(x||0, y||0, z||0);
  me.castShadow = true; me.receiveShadow = true;
  return me;
}
const PANEL_MATS = new Map();                  // teksturaya görə keşlənir ki, birləşdirilə bilsin
function panelMesh(w,h,tex,x,y,z,ry){          // işıq saçan ekran səthi
  if(!PANEL_MATS.has(tex)) PANEL_MATS.set(tex, keep(new THREE.MeshStandardMaterial({
    map:tex, emissiveMap:tex, emissive:0xffffff, emissiveIntensity:0.95,
    roughness:0.22, metalness:0, envMapIntensity:0.25
  })));
  const me = new THREE.Mesh(new THREE.PlaneGeometry(w,h), PANEL_MATS.get(tex));
  me.position.set(x,y,z);
  if(ry) me.rotation.y = ry;
  return me;
}

/* Obyektin onlarla kiçik meshini materiala görə tək-tək mesh-ə birləşdirir.
   Çəkiliş çağırışlarının sayını ~8 dəfə azaldır — kadr sürəti üçün həlledicidir. */
function flatten(group){
  group.updateMatrixWorld(true);
  const byMat = new Map();
  group.traverse(o=>{
    if(!o.isMesh) return;
    if(!byMat.has(o.material)) byMat.set(o.material, []);
    const g = o.geometry.clone();
    g.applyMatrix4(o.matrixWorld);
    ['color','tangent','skinIndex','skinWeight'].forEach(a=>{
      if(g.attributes[a]) g.deleteAttribute(a);
    });
    byMat.get(o.material).push(g);
  });
  const out = new THREE.Group();
  byMat.forEach((geos, material)=>{
    const merged = geos.length === 1
      ? geos[0]
      : THREE.BufferGeometryUtils.mergeBufferGeometries(geos, false);
    if(!merged) return;
    if(geos.length > 1) geos.forEach(g => g.dispose());
    // aoMap ikinci UV dəsti tələb edir
    if(merged.attributes.uv && !merged.attributes.uv2)
      merged.setAttribute('uv2', merged.attributes.uv);
    const m = new THREE.Mesh(merged, material);
    m.castShadow = true; m.receiveShadow = true;
    out.add(m);
  });
  // Mənbə qrupundakı birdəfəlik geometriyalar (plane, sphere) artıq lazım deyil
  group.traverse(o=>{ if(o.isMesh && !SHARED.has(o.geometry)) o.geometry.dispose(); });
  return out;
}

/* ------------------------------------------------------------------ OTAQ
   Otaq ölçüsü dəyişəndə tam yenidən qurulur, ona görə burada istifadə olunan
   materiallar modul səviyyəsində bir dəfə yaradılır — hər yenidənqurmada
   yeni material yaratmaq GPU yaddaşını sızdırardı. */
const MAT_WALL  = pbr(TX.wall, {color:0xdfe5eb, side:THREE.DoubleSide});
const MAT_GLASS = keep(new THREE.MeshStandardMaterial({
  color:0xdcecfb, emissive:0xbcd9f5, emissiveIntensity:0.9,
  roughness:0.08, metalness:0.1, envMapIntensity:0.5,
  transparent:true, opacity:0.92
}));
const MAT_LAMP  = keep(new THREE.MeshStandardMaterial({
  color:0xffffff, emissive:0xfff6e6, emissiveIntensity:1.9, roughness:0.4
}));

function buildRoom(){
  clearGroup(roomGroup);
  const W = S.W, D = S.D, H = S.H;

  /* Döşəmə teksturaları YALNIZ burada işlənir, ona görə təkrarlanma birbaşa
     paylaşılan teksturaya verilir.
     Əvvəllər clone() edilirdi — bu isə yarış şəraiti yaradırdı: şəkil hələ
     yüklənməmişdisə, klonun image sahəsi boş qalırdı (loader yalnız orijinalı
     yeniləyir) və döşəmə metalness=1, xəritəsiz → qapqara render olunurdu. */
  const rep = (t, n)=>{
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(n, n * D / W);
    return t;
  };
  const nx = W/2.2;
  const fgeo = new THREE.PlaneGeometry(W, D);
  fgeo.setAttribute('uv2', fgeo.attributes.uv);
  const floor = new THREE.Mesh(fgeo, new THREE.MeshStandardMaterial({
    map:rep(TX.floor.d, nx), normalMap:rep(TX.floor.n, nx),
    aoMap:rep(TX.floor.a, nx), roughnessMap:rep(TX.floor.a, nx), metalnessMap:rep(TX.floor.a, nx),
    color:0xc4ccd4, roughness:1, metalness:1
  }));
  floor.rotation.x = -Math.PI/2;
  floor.position.set(W/2, 0, D/2);
  floor.receiveShadow = true;
  floor.userData.isFloor = true;
  roomGroup.add(floor);

  const grid = new THREE.GridHelper(Math.max(W,D), Math.max(W,D), 0x64748a, 0x7f8fa2);
  grid.position.set(W/2, 0.004, D/2);
  grid.material.opacity = 0.22; grid.material.transparent = true;
  roomGroup.add(grid);

  const wm  = MAT_WALL;
  const skb = mat(0x9aa6b2, {roughness:0.7});          // plintus
  const t = 0.12;
  const walls = new THREE.Group();
  // Hər divar ayrıca qrupdur ki, kameraya yaxın olanlar avtomatik gizlənə bilsin
  const side = {};
  ['z0','zD','x0','xW'].forEach(k=>{ side[k] = new THREE.Group(); side[k].name = 'side_'+k; walls.add(side[k]); });

  side.z0.add(box(W+t*2, H, t, wm, W/2, H/2, -t/2));
  side.zD.add(box(W+t*2, H, t, wm, W/2, H/2, D+t/2));
  side.x0.add(box(t, H, D, wm, -t/2, H/2, D/2));
  side.xW.add(box(t, H, D, wm, W+t/2, H/2, D/2));

  side.z0.add(box(W, 0.09, 0.02, skb, W/2, 0.045, 0.012));
  side.zD.add(box(W, 0.09, 0.02, skb, W/2, 0.045, D-0.012));
  side.x0.add(box(0.02, 0.09, D, skb, 0.012, 0.045, D/2));
  side.xW.add(box(0.02, 0.09, D, skb, W-0.012, 0.045, D/2));

  // pəncərə lentləri (x = 0 divarı) — otağa gündüz işığı hissi verir
  const glass = MAT_GLASS;
  const frame = mat(0x59636e, {roughness:0.5, metalness:0.3});
  [D*0.28, D*0.68].forEach(zc=>{
    side.x0.add(box(0.03, 1.30, 1.90, glass, 0.055, 1.62, zc));
    side.x0.add(box(0.05, 1.42, 0.07, frame, 0.05, 1.62, zc - 0.95));
    side.x0.add(box(0.05, 1.42, 0.07, frame, 0.05, 1.62, zc + 0.95));
    side.x0.add(box(0.05, 0.07, 1.97, frame, 0.05, 1.62 - 0.68, zc));
    side.x0.add(box(0.05, 0.07, 1.97, frame, 0.05, 1.62 + 0.68, zc));
    side.x0.add(box(0.05, 0.07, 1.90, frame, 0.05, 1.62, zc));
  });
  // Divarlar kölgə salmır — əks halda otağın içi qaralır
  walls.traverse(m => { if(m.isMesh){ m.castShadow = false; m.receiveShadow = true; } });
  walls.name = 'walls';
  walls.visible = S.showWalls;
  roomGroup.add(walls);

  sun.target.position.set(W/2, 0, D/2);
  sun.target.updateMatrixWorld();

  // Tavan və işıq panelləri — yalnız gəzinti rejimində görünür,
  // əks halda yuxarıdan baxışı bağlayardı.
  const ceil = new THREE.Group();
  ceil.name = 'ceiling';
  const cm = mat(0xf4f7fa, {roughness:0.96, side:THREE.DoubleSide});
  const cp = new THREE.Mesh(new THREE.PlaneGeometry(W, D), cm);
  cp.rotation.x = Math.PI/2; cp.position.set(W/2, H, D/2);
  ceil.add(cp);
  const lamp = MAT_LAMP;
  const {cols, rows} = ceilingGrid();
  for(let i=0;i<cols;i++) for(let j=0;j<rows;j++){
    const lx = (i+0.5)*W/cols, lz = (j+0.5)*D/rows;
    ceil.add(box(1.20, 0.05, 0.35, lamp, lx, H-0.03, lz));
    ceil.add(box(1.34, 0.06, 0.46, mat(0xdfe6ec), lx, H-0.005, lz));
  }
  ceil.visible = false;
  roomGroup.add(ceil);

  // ölçü zolaqları döşəmənin kənarında
  const em = mat(0x5d6d7e);
  roomGroup.add(box(W, 0.006, 0.025, em, W/2, 0.006, -0.14));
  roomGroup.add(box(0.025, 0.006, D, em, -0.14, 0.006, D/2));
}

/* ------------------------------------------------------------------ DETALLAR */
function deskTop(w,d,h){
  const g = new THREE.Group();
  g.add(box(w, 0.032, d, MAT_WOOD, 0, h, 0));                       // laminat səth
  g.add(box(w+0.008, 0.014, d+0.008, MAT_EDGE, 0, h-0.022, 0));     // kənar zolaq
  const lx = w/2-0.09, lz = d/2-0.08;
  [[-lx,-lz],[lx,-lz],[-lx,lz],[lx,lz]].forEach(p=>{
    g.add(box(0.042, h-0.05, 0.042, MAT_METAL, p[0], (h-0.05)/2+0.02, p[1]));
    g.add(box(0.09, 0.02, 0.09, MAT_DARK, p[0], 0.01, p[1]));       // ayaq altlığı
  });
  g.add(box(w-0.20, 0.10, 0.03, MAT_PLASTIC, 0, h-0.16, -d/2+0.05));// kabel kanalı
  return g;
}

function monitor(){                       // ekran +z tərəfə baxır
  const g = new THREE.Group();
  const tex = TEX_SCREENS[(Math.random()*TEX_SCREENS.length)|0];
  g.add(cyl(0.105, 0.016, MAT_DARK, 0, 0.008, 0, 24));
  g.add(box(0.05, 0.20, 0.035, MAT_DARK, 0, 0.11, -0.01));
  const head = new THREE.Group();
  head.add(box(0.545, 0.335, 0.016, MAT_DARK, 0, 0, 0));            // korpus
  head.add(box(0.525, 0.315, 0.004, MAT_SCREEN, 0, 0.006, 0.009));  // şüşə
  head.add(panelMesh(0.515, 0.295, tex, 0, 0.008, 0.0125));
  head.position.set(0, 0.365, 0.012);
  head.rotation.x = -0.07;                                          // yüngül maillik
  g.add(head);
  return g;
}

function chair(){                         // arxalıq -z tərəfdə
  const g = new THREE.Group();
  for(let i=0;i<5;i++){                                             // beşguşəli ayaq
    const a = i/5*Math.PI*2;
    const arm = box(0.045, 0.03, 0.30, MAT_PLASTIC,
                    Math.sin(a)*0.15, 0.055, Math.cos(a)*0.15);
    arm.rotation.y = a; g.add(arm);
    g.add(cyl(0.028, 0.055, MAT_DARK, Math.sin(a)*0.285, 0.028, Math.cos(a)*0.285, 10));
  }
  g.add(cyl(0.045, 0.28, MAT_METAL, 0, 0.20, 0, 14));               // qaz lifti
  g.add(cyl(0.055, 0.06, MAT_PLASTIC, 0, 0.36, 0, 14));
  g.add(box(0.46, 0.075, 0.44, MAT_CHAIR, 0, 0.435, 0));            // oturacaq
  g.add(box(0.42, 0.03, 0.40, MAT_MESH, 0, 0.475, 0));
  const back = new THREE.Group();                                    // arxalıq
  back.add(box(0.44, 0.50, 0.045, MAT_CHAIR, 0, 0, 0));
  back.add(box(0.38, 0.42, 0.02, MAT_MESH, 0, 0.01, 0.028));
  back.position.set(0, 0.73, -0.20);
  back.rotation.x = 0.12;
  g.add(back);
  [-0.26, 0.26].forEach(x=>{                                        // qoltuqlar
    g.add(box(0.05, 0.20, 0.05, MAT_PLASTIC, x, 0.55, -0.07));
    g.add(box(0.07, 0.035, 0.24, MAT_PLASTIC, x, 0.665, -0.02));
  });
  return g;
}

function stool(){
  const g = new THREE.Group();
  for(let i=0;i<4;i++){
    const a = i/4*Math.PI*2 + 0.4;
    const arm = box(0.04, 0.028, 0.26, MAT_PLASTIC, Math.sin(a)*0.13, 0.05, Math.cos(a)*0.13);
    arm.rotation.y = a; g.add(arm);
  }
  g.add(cyl(0.032, 0.58, MAT_METAL, 0, 0.31, 0, 12));
  g.add(cyl(0.185, 0.055, MAT_CHAIR, 0, 0.63, 0, 20));
  g.add(cyl(0.20, 0.02, MAT_METAL, 0, 0.22, 0, 20));                // ayaq halqası
  return g;
}

function keyboard(){
  const g = new THREE.Group();
  g.add(box(0.44, 0.016, 0.15, MAT_PLASTIC, 0, 0.008, 0));
  const m = new THREE.MeshStandardMaterial({map:TEX_KEYS, roughness:0.7});
  const k = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.135), m);
  k.rotation.x = -Math.PI/2; k.position.y = 0.017;
  g.add(k);
  return g;
}
function mouse(){
  const m = new THREE.Mesh(new THREE.SphereGeometry(0.045, 14, 10), MAT_PLASTIC);
  m.scale.set(1, 0.62, 1.45); m.position.y = 0.026;
  m.castShadow = true;
  return m;
}
function pc(m){
  const g = new THREE.Group();
  g.add(box(0.19, 0.42, 0.44, m || MAT_PLASTIC, 0, 0.21, 0));
  g.add(box(0.015, 0.30, 0.30, mat(0x20262e), 0.10, 0.24, 0.02));
  g.add(box(0.022, 0.022, 0.012, mat(0x3fd07a, {emissive:0x2ecc71, emissiveIntensity:2.4}),
            0, 0.37, 0.223));
  return g;
}
/* iş yeri dəsti: klaviatura + siçan (masanın üstünə qoyulur) */
function deskKit(g, x, y, z, faceZ){
  const kb = keyboard();
  kb.position.set(x, y, z + faceZ*0.17);
  kb.rotation.y = faceZ > 0 ? 0 : Math.PI;
  g.add(kb);
  const ms = mouse();
  ms.position.set(x + faceZ*0.28, y, z + faceZ*0.17);
  g.add(ms);
}

/* ------------------------------------------------------------------ QURUCULAR */
const BUILD = {

  pod(def){
    const g = new THREE.Group(), w = def.w, d = def.d, h = 0.75;
    g.add(deskTop(w, d, h));
    [[-0.46,-0.20,-1],[0.46,-0.20,-1],[-0.46,0.20,1],[0.46,0.20,1]].forEach(p=>{
      const m0 = monitor();
      m0.position.set(p[0], h+0.032, p[1]);
      m0.rotation.y = p[2] > 0 ? 0 : Math.PI;
      g.add(m0);
      deskKit(g, p[0], h+0.033, p[1], p[2]);
    });
    [[-0.46,-0.86,0],[0.46,-0.86,0],[-0.46,0.86,Math.PI],[0.46,0.86,Math.PI]].forEach(p=>{
      const c = chair(); c.position.set(p[0], 0, p[1]); c.rotation.y = p[2]; g.add(c);
    });
    [[-0.76,-0.30],[0.76,-0.30],[-0.76,0.30],[0.76,0.30]].forEach(p=>{
      const u = pc(); u.position.set(p[0], 0, p[1]); g.add(u);
    });
    return g;
  },

  /* Əlçatan iş yeri — hündürlüyü tənzimlənən masa, oturacaq yoxdur
     (əlil arabası masanın altına girir), döşəmədə nişan.                */
  a11y(def){
    const g = new THREE.Group(), h = 0.78;
    g.add(box(def.w, 0.032, def.d, MAT_WOOD, 0, h, 0));
    g.add(box(def.w+0.008, 0.014, def.d+0.008, MAT_EDGE, 0, h-0.022, 0));
    // teleskopik ayaqlar — masa altı boşluq açıq qalır
    [[-def.w/2+0.12, 0],[def.w/2-0.12, 0]].forEach(p=>{
      g.add(box(0.09, h-0.05, 0.09, MAT_METAL, p[0], (h-0.05)/2, -def.d/2+0.12));
      g.add(box(0.13, 0.02, 0.13, MAT_DARK, p[0], 0.01, -def.d/2+0.12));
      g.add(box(0.05, 0.05, def.d-0.20, MAT_METAL, p[0], h-0.10, 0));
    });
    g.add(box(0.10, 0.05, 0.03, mat(0x2ecc71, {emissive:0x27ae60, emissiveIntensity:1.2}),
              def.w/2-0.22, h+0.04, def.d/2-0.06));           // hündürlük idarəetməsi
    const m0 = monitor(); m0.position.set(0, h+0.032, -0.12); m0.rotation.y = Math.PI; g.add(m0);
    deskKit(g, 0, h+0.033, -0.12, -1);
    g.add(box(0.10, 0.05, 0.03, MAT_PLASTIC, -def.w/2+0.28, h+0.04, def.d/2-0.06));
    // döşəmə nişanı — Ø1,5 m manevr dairəsi, istifadəçi tərəfində
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(0.70, 0.75, 48),
      new THREE.MeshBasicMaterial({color:0x2980b9, side:THREE.DoubleSide,
                                   transparent:true, opacity:0.85})
    );
    ring.rotation.x = -Math.PI/2;
    ring.position.set(0, 0.012, -0.85);
    g.add(ring);
    return g;
  },

  desk1(def){
    const g = new THREE.Group(), h = 0.75;
    g.add(deskTop(def.w, def.d, h));
    const m0 = monitor(); m0.position.set(0, h+0.032, -0.10); m0.rotation.y = Math.PI; g.add(m0);
    deskKit(g, 0, h+0.033, -0.10, -1);
    const c = chair(); c.position.set(0, 0, -0.78); g.add(c);
    const u = pc(); u.position.set(0.44, 0, 0.02); g.add(u);
    return g;
  },

  teacher(def){
    const g = new THREE.Group(), h = 0.75;
    g.add(deskTop(def.w, def.d, h));
    [-0.40, 0.34].forEach(x=>{
      const m0 = monitor(); m0.position.set(x, h+0.032, -0.06); m0.rotation.y = Math.PI; g.add(m0);
    });
    deskKit(g, -0.40, h+0.033, -0.06, -1);
    const c = chair(); c.position.set(-0.10, 0, -0.74); g.add(c);
    const u = pc(); u.position.set(0.78, 0, 0.06); g.add(u);
    return g;
  },

  gpu(def){
    const g = new THREE.Group(), h = 0.75;
    g.add(deskTop(def.w, def.d, h));
    const m0 = monitor(); m0.position.set(-0.16, h+0.032, -0.08); m0.rotation.y = Math.PI; g.add(m0);
    deskKit(g, -0.16, h+0.033, -0.08, -1);
    g.add(box(0.26, 0.56, 0.56, mat(0x272c36, {roughness:0.45}), 0.42, 0.28, 0));
    g.add(box(0.012, 0.40, 0.40, mat(0x14171d), 0.29, 0.30, 0.02));       // şüşə yan panel
    g.add(box(0.03, 0.34, 0.03, mat(0xb06cd8, {emissive:0x8e44ad, emissiveIntensity:2.2}), 0.283, 0.30, -0.10));
    g.add(cyl(0.075, 0.02, mat(0x3a4150), 0.283, 0.46, 0.10, 16).rotateZ(Math.PI/2));
    const c = chair(); c.position.set(-0.16, 0, -0.76); g.add(c);
    return g;
  },

  byod(def){
    const g = new THREE.Group(), h = 0.74, rx = def.w/2, rz = def.d/2;
    const top = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 0.045, 48),
                               mat(0xb5534a, {roughness:0.5}));
    top.scale.set(rx, 1, rz); top.position.y = h;
    top.castShadow = true; top.receiveShadow = true; g.add(top);
    const rim = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 0.022, 48), MAT_EDGE);
    rim.scale.set(rx*1.012, 1, rz*1.012); rim.position.y = h - 0.03; g.add(rim);
    g.add(cyl(0.12, h-0.05, MAT_METAL, 0, (h-0.05)/2, 0, 20));
    const base = new THREE.Mesh(new THREE.CylinderGeometry(1,1,0.04,32), MAT_DARK);
    base.scale.set(rx*0.55, 1, rz*0.55); base.position.y = 0.02; g.add(base);
    // güc/USB modulu masanın ortasında
    g.add(cyl(0.11, 0.05, mat(0x2b323c), 0, h+0.045, 0, 20));
    for(let i=0;i<6;i++){
      const a = (i/6)*Math.PI*2 + Math.PI/6;
      const c = chair();
      c.position.set(Math.cos(a)*(rx+0.44), 0, Math.sin(a)*(rz+0.44));
      c.rotation.y = -a + Math.PI/2;
      g.add(c);
      const lap = box(0.32, 0.015, 0.22, mat(0xa9b4bf, {roughness:0.35, metalness:0.6}),
                      Math.cos(a)*rx*0.62, h+0.03, Math.sin(a)*rz*0.62);
      lap.rotation.y = -a + Math.PI/2; g.add(lap);
      const scr = box(0.32, 0.21, 0.012, mat(0x1a2029),
                      Math.cos(a)*rx*0.36, h+0.13, Math.sin(a)*rz*0.36);
      scr.rotation.y = -a + Math.PI/2; scr.rotation.x = 0.22; g.add(scr);
    }
    return g;
  },

  iot(def){
    const g = new THREE.Group(), w = def.w, d = def.d, h = 0.92;
    g.add(box(w, 0.05, d, mat(0x1d8a74, {roughness:0.35}), 0, h, 0));   // antistatik səth
    g.add(box(w+0.01, 0.02, d+0.01, mat(0x14705e), 0, h-0.032, 0));
    [-w/2+0.12, 0, w/2-0.12].forEach(x=>{
      g.add(box(0.06, h-0.05, d-0.10, MAT_METAL, x, (h-0.05)/2, 0));
    });
    g.add(box(w-0.2, 0.03, d-0.14, mat(0x8b98a5), 0, 0.30, 0));         // alt rəf
    // alət rəfi
    g.add(box(w, 0.035, 0.22, mat(0x24997f), 0, h+0.48, -d/2+0.10));
    [-w/2+0.14, w/2-0.14].forEach(x=> g.add(box(0.04, 0.48, 0.04, MAT_METAL, x, h+0.24, -d/2+0.10)));
    g.add(box(w-0.3, 0.02, 0.02, MAT_METAL, 0, h+0.30, -d/2+0.03));     // alət tutacağı
    for(let i=0;i<6;i++){
      const st = stool();
      st.position.set(-w/2 + 0.32 + i*((w-0.64)/5), 0, d/2 + 0.44);
      g.add(st);
    }
    // ossiloskop, lehimləmə stansiyası, komponent qutuları
    g.add(box(0.34, 0.24, 0.22, mat(0x37414d), -1.15, h+0.145, -0.04));
    g.add(panelMesh(0.26, 0.16, TEX_SCREENS[2], -1.15, h+0.16, 0.075));
    g.add(box(0.20, 0.10, 0.16, mat(0x4a5666), -0.45, h+0.075, 0.02));
    g.add(cyl(0.012, 0.20, mat(0xc0392b), -0.30, h+0.10, 0.06, 8).rotateZ(0.5));
    [[0.30,0xe74c3c],[0.62,0xf1c40f],[0.94,0x3498db],[1.26,0x2ecc71]].forEach(p=>
      g.add(box(0.26, 0.085, 0.17, mat(p[1], {roughness:0.6}), p[0], h+0.068, 0.02)));
    return g;
  },

  rack(def){
    const g = new THREE.Group();
    g.add(box(def.w, def.h, def.d, mat(0x2f3640, {roughness:0.45, metalness:0.35}), 0, def.h/2, 0));
    g.add(box(def.w-0.06, def.h-0.12, 0.02, mat(0x14181e), 0, def.h/2, def.d/2+0.002));
    for(let i=0;i<9;i++){
      const y = 0.26 + i*0.19;
      g.add(box(def.w-0.14, 0.155, 0.03, mat(0x424b57, {roughness:0.4, metalness:0.5}), 0, y, def.d/2+0.012));
      g.add(box(def.w-0.30, 0.055, 0.012, mat(0x1b1f26), 0, y+0.03, def.d/2+0.028));
      for(let k=0;k<3;k++)
        g.add(box(0.022, 0.022, 0.012, mat(k===0?0x2ecc71:0x3498db,
                  {emissive:k===0?0x27ae60:0x2980b9, emissiveIntensity:2.2}),
                  def.w/2-0.10-k*0.045, y-0.045, def.d/2+0.03));
    }
    g.add(box(def.w+0.03, 0.04, def.d+0.03, mat(0x22272e), 0, def.h-0.02, 0));
    return g;
  },

  ups(def){
    const g = new THREE.Group();
    g.add(box(def.w, def.h, def.d, mat(0x6c3483), 0, def.h/2, 0));
    g.add(box(def.w-0.16, 0.16, 0.02, MAT_SCREEN, 0, def.h-0.22, def.d/2+0.005));
    return g;
  },

  nas(def){
    const g = new THREE.Group();
    g.add(box(def.w, def.h, def.d, mat(0x5b2c6f), 0, def.h/2, 0));
    for(let i=0;i<4;i++)
      g.add(box(def.w-0.10, 0.07, 0.02, mat(0x34495e), 0, 0.07+i*0.09, def.d/2+0.005));
    return g;
  },

  printer(def){
    const g = new THREE.Group();
    g.add(box(def.w, 0.72, def.d, mat(0x6d7b88), 0, 0.36, 0));
    g.add(box(0.52, 0.50, 0.50, mat(0x455565), -0.34, 0.97, 0));            // 3D printer
    g.add(box(0.44, 0.40, 0.42, mat(0x2f3b47), -0.34, 0.97, 0.03));
    g.add(box(0.60, 0.34, 0.50, mat(0x39424c), 0.34, 0.89, 0));             // MFP
    g.add(box(0.44, 0.02, 0.30, mat(0xecf0f1), 0.34, 1.07, 0.05));
    return g;
  },

  cabinet(def){
    const g = new THREE.Group();
    g.add(box(def.w, def.h, def.d, mat(0x8b98a5), 0, def.h/2, 0));
    [0.45, 1.35].forEach(y=>{
      g.add(box(def.w-0.06, 0.02, 0.02, mat(0x5d6d7e), 0, y, def.d/2+0.006));
      g.add(box(0.05, 0.12, 0.03, MAT_METAL, def.w/2-0.14, y+0.22, def.d/2+0.02));
    });
    return g;
  },

  panel(def){
    const g = new THREE.Group(), cy = def.my + def.h/2;
    g.add(box(def.w, def.h, def.d, mat(0x171d24, {roughness:0.4, metalness:0.3}), 0, cy, 0));
    g.add(box(def.w-0.06, def.h-0.06, 0.01, MAT_SCREEN, 0, cy, def.d/2+0.004));
    g.add(panelMesh(def.w-0.09, def.h-0.09, TEX_SCREENS[1], 0, cy, def.d/2+0.012));
    g.add(box(0.34, 0.05, 0.06, mat(0x3a444f), 0, def.my-0.06, def.d/2-0.02));  // divar bərkidicisi
    return g;
  },

  screen55(def){
    const g = new THREE.Group(), cy = def.my + def.h/2;
    g.add(box(def.w, def.h, def.d, mat(0x171d24, {roughness:0.4, metalness:0.3}), 0, cy, 0));
    g.add(box(def.w-0.05, def.h-0.05, 0.01, MAT_SCREEN, 0, cy, def.d/2+0.004));
    g.add(panelMesh(def.w-0.07, def.h-0.07, TEX_SCREENS[0], 0, cy, def.d/2+0.012));
    return g;
  },

  ac(def){
    const g = new THREE.Group(), cy = def.my + def.h/2;
    g.add(box(def.w, def.h, def.d, mat(0xf0f6fb, {roughness:0.45}), 0, cy, 0));
    g.add(box(def.w-0.02, 0.05, 0.03, mat(0xcfdde8), 0, cy+def.h/2-0.05, def.d/2+0.002));
    for(let i=0;i<5;i++)                                        // jalüz dilimləri
      g.add(box(def.w-0.10, 0.016, 0.02, mat(0xa9bdcd), 0, def.my+0.05+i*0.028, def.d/2-0.01));
    g.add(box(0.10, 0.02, 0.02, mat(0x2ecc71, {emissive:0x27ae60, emissiveIntensity:1.4}),
              def.w/2-0.12, def.my+0.02, def.d/2+0.002));
    return g;
  }
};

/* ------------------------------------------------------------------ OBYEKTLƏR */
const ZONE_GEO = keep(new THREE.PlaneGeometry(1,1));   // bütün keçid zonaları üçün ortaq

function addObject(type, x, z, rotDeg, silent){
  const def = CATALOG[type];
  if(!def) return null;
  const g = flatten(BUILD[type](def));
  g.userData.objId = S.nextId;
  objGroup.add(g);

  const o = {
    id:S.nextId++, type, def,
    x: x!==undefined ? x : S.W/2,
    z: z!==undefined ? z : S.D/2,
    rot:(rotDeg||0) * Math.PI/180,
    group:g, zone:null
  };
  S.objects.push(o);

  if(def.cx > 0 || def.cz > 0){
    // həndəsə paylaşılır (miqyasla ölçülür), material fərdidir — rəngi obyektə görə dəyişir
    const zm = new THREE.Mesh(
      ZONE_GEO,
      new THREE.MeshBasicMaterial({color:0x2ecc71, transparent:true, opacity:0.11,
                                   side:THREE.DoubleSide, depthWrite:false})
    );
    zm.rotation.x = -Math.PI/2;
    zoneGroup.add(zm);
    o.zone = zm;
  }
  applyTransform(o);
  if(!silent) refresh();
  return o;
}

function applyTransform(o){
  o.group.position.set(o.x, 0, o.z);
  o.group.rotation.y = o.rot;
  if(o.zone){
    const d = o.def;
    o.zone.scale.set(d.w + d.cx*2, d.d + d.cz*2, 1);
    o.zone.position.set(o.x, 0.012, o.z);
    o.zone.rotation.set(-Math.PI/2, 0, -o.rot);
  }
}

function removeObject(o){
  objGroup.remove(o.group);
  disposeTree(o.group);                    // birləşdirilmiş geometriya fərdidir — azad olunur
  if(o.zone){ zoneGroup.remove(o.zone); disposeTree(o.zone); }
  S.objects = S.objects.filter(k => k !== o);
  if(S.selected === o) select(null);
}

/* ------------------------------------------------------------------ HƏNDƏSƏ */
function aabb(o){
  const c = Math.abs(Math.cos(o.rot)), s = Math.abs(Math.sin(o.rot));
  const hw = o.def.w/2, hd = o.def.d/2;
  const ex = hw*c + hd*s, ez = hw*s + hd*c;
  return {x0:o.x-ex, x1:o.x+ex, z0:o.z-ez, z1:o.z+ez, ex, ez};
}
/* 90°-lik dönmədə oturacaq tərəfi də dönür — boşluq tələbi yerini dəyişir */
function clears(o){
  const q = Math.abs(Math.round(o.rot / (Math.PI/2))) % 2;
  return q === 0 ? {cx:o.def.cx, cz:o.def.cz} : {cx:o.def.cz, cz:o.def.cx};
}

/* Obyektin şaquli əhatəsi (m). Divara quraşdırılanlar döşəmədən yuxarıda asılır,
   ona görə plan üzrə kəsişmələri tək başına toqquşma demək deyil:
   86" panel masanın üstündən keçə bilər, amma 2 m-lik rack ilə toqquşur. */
function vRange(o){
  const d = o.def;
  return d.wall ? [d.my, d.my + d.h] : [0, d.h || 1.15];
}
function vOverlap(a, b){
  const A = vRange(a), B = vRange(b);
  return Math.min(A[1], B[1]) - Math.max(A[0], B[0]) > 0.02;
}

/* İki obyektin münasibəti: üst-üstə düşür / keçid dardır / qaydadadır */
function pairCheck(a, b){
  const A = aabb(a), B = aabb(b);
  const gx = Math.max(A.x0 - B.x1, B.x0 - A.x1);
  const gz = Math.max(A.z0 - B.z1, B.z0 - A.z1);
  const wallPair = a.def.wall || b.def.wall;

  if(gx < 0 && gz < 0) return {overlap: !wallPair || vOverlap(a, b), tight:false};

  // Divara asılan obyekt döşəmədə yer tutmur — keçid yolu tələbi ona aid deyil.
  if(wallPair) return {overlap:false, tight:false};

  // İki avadanlıq yan-yana dura bilər — keçid yolu yalnız insan oturan
  // mövqelərə aiddir, ona görə avadanlıq–avadanlıq cütü yoxlanmır.
  if(a.def.equip && b.def.equip) return {overlap:false, tight:false};

  const ca = clears(a), cb = clears(b);
  // Ayrılma yalnız bir ox üzrədirsə, həmin oxun boşluq tələbi tətbiq olunur.
  // Hər iki ox üzrə ayrılıblarsa (künc vəziyyəti) keçid yolu tələb olunmur.
  if(gx >= 0 && gz >= 0 && gx > 0.001 && gz > 0.001) return {overlap:false, tight:false};

  const need = gz < 0 ? ca.cx + cb.cx : ca.cz + cb.cz;
  const gap  = gz < 0 ? gx : gz;
  return {overlap:false, tight: need > 0 && gap < need - 0.005};
}
function overlaps(a, b){ return pairCheck(a, b).overlap; }

/* ------------------------------------------------------------------ SEÇİM */
function select(o){
  S.selected = o;
  if(!o){ selBox.visible = false; }
  else{
    const d = o.def, h = d.h || (d.wall ? d.my + d.h : 1.15);
    const height = d.wall ? d.h : h;
    const cy = d.wall ? d.my + d.h/2 : height/2;
    selBox.geometry.dispose();
    selBox.geometry = new THREE.EdgesGeometry(new THREE.BoxGeometry(d.w+0.06, height+0.06, d.d+0.06));
    selBox.position.set(o.x, cy, o.z);
    selBox.rotation.y = o.rot;
    selBox.visible = true;
  }
  renderSelPanel();
}
function updateSelBox(){
  if(!S.selected) return;
  selBox.position.set(S.selected.x, selBox.position.y, S.selected.z);
  selBox.rotation.y = S.selected.rot;
}

/* ------------------------------------------------------------------ SÜRÜKLƏMƏ */
const ray = new THREE.Raycaster();
const ptr = new THREE.Vector2();
const plane = new THREE.Plane(new THREE.Vector3(0,1,0), 0);
const hit = new THREE.Vector3();
let dragging = null, dragOff = new THREE.Vector3(), moved = false;

function pointerNDC(e){
  const r = renderer.domElement.getBoundingClientRect();
  ptr.x = ((e.clientX - r.left)/r.width)*2 - 1;
  ptr.y = -((e.clientY - r.top)/r.height)*2 + 1;
}
function pickObject(){
  ray.setFromCamera(ptr, camera);
  const its = ray.intersectObjects(objGroup.children, true);
  if(!its.length) return null;
  let n = its[0].object;
  while(n && n.userData.objId === undefined) n = n.parent;
  if(!n) return null;
  return S.objects.find(o => o.id === n.userData.objId) || null;
}
function snapVal(v){ return S.snap > 0 ? Math.round(v/S.snap)*S.snap : v; }

/* Divar obyektlərini ən yaxın divara oturdur */
function snapWall(o){
  const cand = [
    {d:o.z,        x:o.x, z:0,    r:0},
    {d:S.D - o.z,  x:o.x, z:S.D,  r:Math.PI},
    {d:o.x,        x:0,   z:o.z,  r:Math.PI/2},
    {d:S.W - o.x,  x:S.W, z:o.z,  r:-Math.PI/2}
  ].sort((a,b)=> a.d - b.d)[0];
  o.x = cand.x; o.z = cand.z; o.rot = cand.r;
  const half = o.def.w/2;
  if(cand.r === 0 || cand.r === Math.PI) o.x = Math.min(Math.max(o.x, half), S.W - half);
  else                                   o.z = Math.min(Math.max(o.z, half), S.D - half);
}

renderer.domElement.addEventListener('pointerdown', e=>{
  if(e.button !== 0 || S.mode === 'walk') return;
  pointerNDC(e);
  const o = pickObject();
  select(o);
  if(o){
    ray.setFromCamera(ptr, camera);
    if(ray.ray.intersectPlane(plane, hit)){
      dragOff.set(hit.x - o.x, 0, hit.z - o.z);
      dragging = o; moved = false;
      controls.enabled = false;
      renderer.domElement.style.cursor = 'grabbing';
    }
  }
});

renderer.domElement.addEventListener('pointermove', e=>{
  if(S.mode === 'walk') return;
  if(!dragging){
    pointerNDC(e);
    renderer.domElement.style.cursor = pickObject() ? 'grab' : 'default';
    return;
  }
  if(!moved){ pushUndo(); moved = true; }
  pointerNDC(e);
  ray.setFromCamera(ptr, camera);
  if(!ray.ray.intersectPlane(plane, hit)) return;

  dragging.x = snapVal(hit.x - dragOff.x);
  dragging.z = snapVal(hit.z - dragOff.z);

  if(dragging.def.wall) snapWall(dragging);
  else{
    const a = aabb(dragging);
    dragging.x = Math.min(Math.max(dragging.x, a.ex), S.W - a.ex);
    dragging.z = Math.min(Math.max(dragging.z, a.ez), S.D - a.ez);
  }
  applyTransform(dragging);
  updateSelBox();
  refresh();
});

addEventListener('pointerup', ()=>{
  if(dragging){
    dragging = null;
    controls.enabled = true;
    renderer.domElement.style.cursor = 'default';
    refresh();
  }
});

/* ------------------------------------------------------------------ KLAVİATURA */
addEventListener('keydown', e=>{
  if(/^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName)) return;
  const k = e.key.toLowerCase();

  if(e.ctrlKey && k === 'z'){ e.preventDefault(); popUndo(); return; }
  if(e.ctrlKey && k === 'd'){ e.preventDefault(); duplicate(); return; }
  if(k === 'escape'){ select(null); return; }

  if(S.mode === 'walk') return;
  if(!S.selected) return;

  if(k === 'q' || k === 'e'){
    pushUndo();
    S.selected.rot += (k === 'q' ? -1 : 1) * Math.PI/12;
    if(S.selected.def.wall) snapWall(S.selected);
    applyTransform(S.selected); updateSelBox(); refresh();
  }
  if(k === 'delete' || k === 'backspace'){
    e.preventDefault(); pushUndo(); removeObject(S.selected); refresh();
  }
});

function duplicate(){
  if(!S.selected) return;
  pushUndo();
  const s = S.selected;
  const n = addObject(s.type, s.x + 0.6, s.z + 0.6, s.rot*180/Math.PI, true);
  select(n); refresh();
}

/* ------------------------------------------------------------------ GERİ AL */
function serialize(){
  return S.objects.map(o => ({t:o.type, x:+o.x.toFixed(3), z:+o.z.toFixed(3),
                              r:+(o.rot*180/Math.PI).toFixed(1)}));
}
function pushUndo(){
  S.undo.push({W:S.W, D:S.D, H:S.H, items:serialize()});
  if(S.undo.length > 60) S.undo.shift();
}
function popUndo(){
  const st = S.undo.pop();
  if(!st) return;
  loadLayout(st.items, st.W, st.D, true, st.H);
}
function loadLayout(items, W, D, noUndo, H){
  if(!noUndo) pushUndo();
  [...S.objects].forEach(removeObject);
  if(W){ S.W = W; document.getElementById('roomW').value = W; }
  if(D){ S.D = D; document.getElementById('roomD').value = D; }
  if(H){ S.H = H; document.getElementById('roomH').value = H; }
  buildRoom();
  items.forEach(i => addObject(i.t, i.x, i.z, i.r, true));
  select(null);
  refresh();
}

/* ------------------------------------------------------------------ YOXLAMA */
function refresh(){
  const seats  = S.objects.reduce((s,o)=> s + o.def.seats, 0);
  const budget = S.objects.reduce((s,o)=> s + o.def.price, 0);
  const area   = S.W * S.D;
  const dens   = seats ? area/seats : 0;

  const bad = new Set();
  const msgs = [];

  // otaqdan kənar — divara quraşdırılan obyektlər yoxlanmır
  S.objects.forEach(o=>{
    if(o.def.wall) return;
    const a = aabb(o);
    if(a.x0 < -0.02 || a.z0 < -0.02 || a.x1 > S.W+0.02 || a.z1 > S.D+0.02){
      bad.add(o.id);
      msgs.push({t:'err', s:`"${o.def.nm}" otaqdan kənara çıxır`});
    }
  });

  // üst-üstə düşmə və keçid yolu
  let narrow = 0;
  for(let i=0;i<S.objects.length;i++)
    for(let j=i+1;j<S.objects.length;j++){
      const a = S.objects[i], b = S.objects[j];
      // Divar obyektləri artıq şaquli əhatəyə görə yoxlanır (bax: pairCheck)
      const r = pairCheck(a, b);
      if(r.overlap){
        bad.add(a.id); bad.add(b.id);
        msgs.push({t:'err', s:`"${a.def.nm}" və "${b.def.nm}" üst-üstə düşür`});
      }else if(r.tight){
        bad.add(a.id); bad.add(b.id); narrow++;
      }
    }
  if(narrow)
    msgs.push({t:'warn', s:`${narrow} yerdə keçid yolu tələb olunandan dardır — stul çəkmək üçün yer qalmır`});

  // zonaların rəngi
  S.objects.forEach(o=>{
    if(!o.zone) return;
    o.zone.visible = S.showZones;
    o.zone.material.color.setHex(bad.has(o.id) ? 0xe74c3c : 0x2ecc71);
    o.zone.material.opacity = bad.has(o.id) ? 0.20 : 0.10;
  });

  // sıxlıq
  if(seats === 0)        msgs.push({t:'warn', s:'Heç bir tələbə iş yeri yoxdur'});
  else if(dens < 1.8)    msgs.push({t:'err',  s:`Sıxlıq ${dens.toFixed(2)} m²/iş yeri — normadan aşağı (min. 1,8)`});
  else if(dens < 2.2)    msgs.push({t:'warn', s:`Sıxlıq ${dens.toFixed(2)} m²/iş yeri — minimum həddə (rahat: 2,2+)`});

  if(!msgs.length) msgs.push({t:'ok', s:'Bütün yoxlamalar keçdi — düzülüş normalara uyğundur'});

  // panellər
  const bcls = seats === 0 ? '' : dens < 1.8 ? 'err' : dens < 2.2 ? 'warn' : 'ok';
  document.getElementById('stats').innerHTML = [
    ['Tələbə iş yeri', seats, ''],
    ['Obyekt sayı', S.objects.length, ''],
    ['Otaq sahəsi', area.toFixed(1) + ' m²', ''],
    ['Sıxlıq', (seats ? dens.toFixed(2) : '—') + ' m²/iş yeri', bcls],
    ['Avadanlıq büdcəsi', budget.toLocaleString('az-AZ').replace(/,/g,' ') + ' AZN', '']
  ].map(r=> `<div class="stat"><span class="k">${r[0]}</span><span class="v ${r[2]}">${r[1]}</span></div>`).join('');

  // Ciddiliyə görə sıralanır ki, xəta xəbərdarlığın arxasında gizlənməsin;
  // siyahı kəsilirsə, neçə mesajın göstərilmədiyi açıq yazılır.
  const rank = {err:0, warn:1, ok:2};
  msgs.sort((m, n)=> rank[m.t] - rank[n.t]);
  const LIMIT = 7;
  const hidden = msgs.length - LIMIT;
  document.getElementById('msgs').innerHTML =
    msgs.slice(0, LIMIT).map(m => `<div class="msg ${m.t}">${m.s}</div>`).join('') +
    (hidden > 0 ? `<div class="msg warn">…və daha ${hidden} bildiriş göstərilmədi</div>` : '');

  renderSelPanel();
  if(typeof buildDims === 'function') buildDims();
  if(typeof renderTechPanels === 'function') renderTechPanels();
  save();
}

/* ------------------------------------------------------------------ SEÇİM PANELİ */
function renderSelPanel(){
  const el = document.getElementById('selBox');
  const o = S.selected;
  if(!o){ el.innerHTML = '<div class="empty">Obyekt seçilməyib</div>'; return; }
  const d = o.def;
  el.innerHTML = `
    <div class="t">${d.nm}</div>
    <div class="row"><span>X</span><input id="px" type="number" step="0.05" value="${o.x.toFixed(2)}"></div>
    <div class="row"><span>Z</span><input id="pz" type="number" step="0.05" value="${o.z.toFixed(2)}"></div>
    <div class="row"><span>°</span><input id="pr" type="number" step="15" value="${Math.round(o.rot*180/Math.PI)}"></div>
    <div class="stat"><span class="k">Ölçü</span><span class="v">${d.w} × ${d.d} m</span></div>
    <div class="stat"><span class="k">İş yeri</span><span class="v">${d.seats}</span></div>
    <div class="stat"><span class="k">Qiymət</span><span class="v">${d.price.toLocaleString('az-AZ').replace(/,/g,' ')} AZN</span></div>
    <div class="btns">
      <button id="bdup">Kopyala</button>
      <button id="bdel" class="danger">Sil</button>
    </div>`;

  const apply = ()=>{
    pushUndo();
    o.x = parseFloat(document.getElementById('px').value) || 0;
    o.z = parseFloat(document.getElementById('pz').value) || 0;
    o.rot = (parseFloat(document.getElementById('pr').value) || 0) * Math.PI/180;
    if(d.wall) snapWall(o);
    applyTransform(o); updateSelBox(); refresh();
  };
  ['px','pz','pr'].forEach(id => document.getElementById(id).addEventListener('change', apply));
  document.getElementById('bdup').onclick = duplicate;
  document.getElementById('bdel').onclick = ()=>{ pushUndo(); removeObject(o); refresh(); };
}

/* ------------------------------------------------------------------ YADDAŞ */
const KEY = 'it-lab-3d-v1';
function save(){
  try{ localStorage.setItem(KEY, JSON.stringify({W:S.W, D:S.D, H:S.H, items:serialize()})); }catch(e){}
}
function restore(){
  try{
    const raw = localStorage.getItem(KEY);
    if(!raw) return false;
    const st = JSON.parse(raw);
    if(!st.items || !st.items.length) return false;
    loadLayout(st.items, st.W, st.D, true, st.H);
    return true;
  }catch(e){ return false; }
}

/* ------------------------------------------------------------------ KATALOQ UI */
const catEl = document.getElementById('catalog');
Object.keys(CATALOG).forEach(type=>{
  const d = CATALOG[type];
  const b = document.createElement('button');
  b.className = 'cat';
  b.innerHTML = `<span class="sw" style="background:#${d.col.toString(16).padStart(6,'0')}"></span>
                 <span class="nm">${d.nm}</span>
                 <span class="pr">${(d.price/1000).toFixed(1)}k</span>`;
  b.onclick = ()=>{
    pushUndo();
    const o = d.wall
      ? addObject(type, S.W/2, S.D, 180, true)
      : addObject(type, S.W/2, S.D/2, 0, true);
    // üst-üstə düşməyən boş yer axtar
    if(!d.wall){
      for(let k=0; k<90 && S.objects.some(q => q !== o && overlaps(o, q)); k++){
        o.x = Math.min(0.8 + (k * 1.4) % Math.max(1, S.W - 1.6), S.W - d.w/2);
        o.z = Math.min(0.8 + Math.floor((k * 1.4) / Math.max(1, S.W - 1.6)) * 1.5, S.D - d.d/2);
        applyTransform(o);
      }
    }
    select(o); refresh();
  };
  catEl.appendChild(b);
});

/* ------------------------------------------------------------------ TOOLBAR */
const $ = id => document.getElementById(id);

$('snap').onchange = e => S.snap = parseFloat(e.target.value);

$('walls').onclick = e=>{
  S.showWalls = !S.showWalls;
  e.target.classList.toggle('on', S.showWalls);
  const w = roomGroup.getObjectByName('walls');
  if(w) w.visible = S.showWalls;
  const c = roomGroup.getObjectByName('ceiling');
  if(c) c.visible = S.showWalls && S.mode === 'walk';
};
$('zones').onclick = e=>{
  S.showZones = !S.showZones;
  e.target.classList.toggle('on', S.showZones);
  refresh();
};
$('dims').onclick = e=>{
  S.showDims = !S.showDims;
  e.target.classList.toggle('on', S.showDims);
  buildDims();
};
$('lux').onclick = e=>{
  S.showLux = !S.showLux;
  e.target.classList.toggle('on', S.showLux);
  renderTechPanels();
};
$('preset').onchange = e=>{ applyPreset(e.target.value); e.target.value = ''; };
$('png4k').onclick = render4K;
$('expParams').onclick = ()=>{
  dl(new Blob([JSON.stringify(paramsJSON(), null, 2)], {type:'application/json'}),
     'lab_parametrleri.json');
};

$('undo').onclick  = popUndo;
$('reset').onclick = ()=> loadLayout(DEFAULT_LAYOUT.map(o=>({t:o.t,x:o.x,z:o.z,r:o.r||0})), DEFAULT_ROOM.W, DEFAULT_ROOM.D, false, DEFAULT_ROOM.H);
$('clear').onclick = ()=>{ pushUndo(); [...S.objects].forEach(removeObject); refresh(); };

['roomW','roomD','roomH'].forEach(id=>{
  $(id).addEventListener('change', ()=>{
    pushUndo();
    S.W = Math.min(Math.max(parseFloat($('roomW').value)||10, 4), 30);
    S.D = Math.min(Math.max(parseFloat($('roomD').value)||7, 4), 30);
    S.H = Math.min(Math.max(parseFloat($('roomH').value)||2.8, 2.4), 5);
    $('roomW').value = S.W; $('roomD').value = S.D; $('roomH').value = S.H;
    buildRoom();
    frameRoom(true);
    refresh();
  });
});

$('expJson').onclick = ()=>{
  dl(new Blob([JSON.stringify(layoutJSON(), null, 2)], {type:'application/json'}),
     'laboratoriya-duzulus.json');
};
$('impJson').onclick = ()=> $('file').click();
$('file').onchange = e=>{
  const f = e.target.files[0]; if(!f) return;
  const r = new FileReader();
  r.onload = ()=>{
    try{
      const j = JSON.parse(r.result);
      const items = (j.obyektler || j.items || []).map(o=>({
        t:o.tip || o.t, x:o.x, z:o.z, r:o.bucaq !== undefined ? o.bucaq : (o.r||0)
      })).filter(o => CATALOG[o.t]);
      if(!items.length) return alert('Faylda tanınan obyekt tapılmadı.');
      const rm = j.otaq || {};
      loadLayout(items, rm.en, rm.uzunluq, false, rm.hundurluk);
    }catch(err){ alert('Fayl oxunmadı: ' + err.message); }
  };
  r.readAsText(f);
  e.target.value = '';
};
/* Ekranda görünən şəkil post-emaldan keçir; ixracın da eyni görünməsi üçün
   composer istifadə olunur — əks halda PNG-də SSAO, bloom və SMAA olmur. */
function renderFrame(){
  if(composer) composer.render(0);
  else renderer.render(scene, camera);
}
$('png').onclick = ()=>{
  renderFrame();
  renderer.domElement.toBlob(b => dl(b, 'laboratoriya-3d.png'));
};
function dl(blob, name){
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
  setTimeout(()=> URL.revokeObjectURL(a.href), 4000);
}

/* ══════════════════════════════════════════════════════════════════
   TEXNİKİ QAT — ölçülər, işıqlanma analizi, elektrik nöqtələri
   ══════════════════════════════════════════════════════════════════ */
const dimGroup = new THREE.Group(); scene.add(dimGroup);
const luxGroup = new THREE.Group(); scene.add(luxGroup);
S.showDims = false;
S.showLux  = false;

function label(text, size){
  const pad = 12, fs = 44;
  const c = document.createElement('canvas');
  const g0 = c.getContext('2d');
  g0.font = `700 ${fs}px Segoe UI, sans-serif`;
  c.width  = Math.ceil(g0.measureText(text).width) + pad*2;
  c.height = fs + pad*2;
  const g = c.getContext('2d');
  g.fillStyle = 'rgba(15,22,32,.88)';
  g.fillRect(0, 0, c.width, c.height);
  g.strokeStyle = '#f1c40f'; g.lineWidth = 3;
  g.strokeRect(1.5, 1.5, c.width-3, c.height-3);
  g.font = `700 ${fs}px Segoe UI, sans-serif`;
  g.fillStyle = '#ffffff'; g.textBaseline = 'middle';
  g.fillText(text, pad, c.height/2 + 2);
  const t = new THREE.CanvasTexture(c);
  t.encoding = THREE.sRGBEncoding;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({map:t, depthTest:false, transparent:true}));
  keep(sp.geometry);          // Sprite həndəsəsi three.js daxilində paylaşılır — azad edilməməlidir
  const s = size || 0.30;
  sp.scale.set(s * c.width / c.height, s, 1);
  sp.renderOrder = 998;
  return sp;
}

function dimLine(a, b, text, y, col){
  const g = new THREE.Group();
  const m = new THREE.LineBasicMaterial({color: col || 0xf1c40f, depthTest:false});
  const pts = [new THREE.Vector3(a.x, y, a.z), new THREE.Vector3(b.x, y, b.z)];
  const ln = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), m);
  ln.renderOrder = 997; g.add(ln);
  // uc çırpıları
  const dir = new THREE.Vector3().subVectors(pts[1], pts[0]).normalize();
  const per = new THREE.Vector3(-dir.z, 0, dir.x).multiplyScalar(0.11);
  [pts[0], pts[1]].forEach(p=>{
    const t = new THREE.Line(new THREE.BufferGeometry().setFromPoints(
      [p.clone().add(per), p.clone().sub(per)]), m);
    t.renderOrder = 997; g.add(t);
  });
  const lb = label(text);
  lb.position.copy(pts[0]).add(pts[1]).multiplyScalar(0.5).setY(y + 0.22);
  g.add(lb);
  return g;
}

function buildDims(){
  clearGroup(dimGroup);            // hər etiket öz kanvas teksturasını daşıyır
  if(!S.showDims) return;

  dimGroup.add(dimLine({x:0, z:-0.55}, {x:S.W, z:-0.55}, S.W.toFixed(1) + ' m', 0.02));
  dimGroup.add(dimLine({x:-0.55, z:0}, {x:-0.55, z:S.D}, S.D.toFixed(1) + ' m', 0.02));

  const lb = label(`${(S.W*S.D).toFixed(1)} m²   ·   ${S.objects.reduce((s,o)=>s+o.def.seats,0)} iş yeri`, 0.5);
  lb.position.set(S.W/2, 2.55, S.D/2);
  dimGroup.add(lb);

  // ən dar keçid yollarını ölçüb göstərir
  const shown = [];
  for(let i=0;i<S.objects.length;i++)
    for(let j=i+1;j<S.objects.length;j++){
      const a = S.objects[i], b = S.objects[j];
      if(a.def.wall || b.def.wall || (a.def.equip && b.def.equip)) continue;
      const A = aabb(a), B = aabb(b);
      const gx = Math.max(A.x0-B.x1, B.x0-A.x1);
      const gz = Math.max(A.z0-B.z1, B.z0-A.z1);
      // Hər fərqli ölçü yalnız bir dəfə göstərilir ki, səhnə oxunaqlı qalsın
      if(gz < 0 && gx > 0.05 && gx < 2.5 && Math.abs(a.z-b.z) < 0.3){
        const bad = gx < a.def.cx + b.def.cx;
        const key = 'x' + gx.toFixed(2) + (bad ? 'B' : '');
        if(shown.indexOf(key) < 0 || bad){ shown.push(key);
          const x0 = Math.min(A.x1, B.x1), x1 = Math.max(A.x0, B.x0);
          dimGroup.add(dimLine({x:x0, z:a.z}, {x:x1, z:a.z}, gx.toFixed(2)+' m', 0.78,
                               bad ? 0xe74c3c : 0x2ecc71)); }
      }
      if(gx < 0 && gz > 0.05 && gz < 2.5 && Math.abs(a.x-b.x) < 0.3){
        const bad = gz < a.def.cz + b.def.cz;
        const key = 'z' + gz.toFixed(2) + (bad ? 'B' : '');
        if(shown.indexOf(key) < 0 || bad){ shown.push(key);
          const z0 = Math.min(A.z1, B.z1), z1 = Math.max(A.z0, B.z0);
          dimGroup.add(dimLine({x:a.x, z:z0}, {x:a.x, z:z1}, gz.toFixed(2)+' m', 0.78,
                               bad ? 0xe74c3c : 0x2ecc71)); }
      }
    }
}

/* ---------- İşıqlanma (lüks) analizi ----------
   Tavan LED panelləri Lambert paylanmalı nöqtəvi mənbə kimi modelləşdirilir:
   E = (Φ/π) · cos⁴θ / h²  ·  MF   —  iş səthi 0,75 m hündürlükdə          */
const LUM_FLUX = 4000;      // bir 1200×300 LED panelin işıq axını (lm)
const MAINT    = 0.80;      // istismar əmsalı
const WORK_H   = 0.75;      // iş səthinin hündürlüyü
const REFL_K   = 0.25;      // divar/tavandan əks olunub iş səthinə düşən pay

/* Tavan panellərinin şəbəkəsi — həm vizual tavan, həm də hesablama
   eyni funksiyadan istifadə edir ki, göstərilən və hesablanan üst-üstə düşsün. */
function ceilingGrid(){
  return {cols: Math.max(2, Math.round(S.W/2.6)), rows: Math.max(2, Math.round(S.D/2.4))};
}
function luminaires(){
  const {cols, rows} = ceilingGrid();
  const out = [];
  for(let i=0;i<cols;i++) for(let j=0;j<rows;j++)
    out.push({x:(i+0.5)*S.W/cols, z:(j+0.5)*S.D/rows});
  return out;
}
/* Birbaşa komponent: Lambert paylanmalı panel, E = (Φ/π)·cos⁴θ/h² */
function luxAt(x, z, lums){
  const h = S.H - WORK_H;
  let E = 0;
  for(const L of lums){
    const d2 = (x-L.x)*(x-L.x) + (z-L.z)*(z-L.z);
    const cos = h / Math.sqrt(d2 + h*h);
    E += (LUM_FLUX/Math.PI) * Math.pow(cos, 4) / (h*h);
  }
  return E * MAINT;
}

function analyseLux(){
  const lums = luminaires();
  // Əks olunan komponent bütün səth üzrə bərabər paylanır (lümen metodu)
  const indirect = lums.length * LUM_FLUX * REFL_K * MAINT / (S.W * S.D);
  const N = 24, vals = [];
  for(let i=0;i<N;i++) for(let j=0;j<N;j++)
    vals.push(luxAt((i+0.5)*S.W/N, (j+0.5)*S.D/N, lums) + indirect);
  const min = Math.min(...vals), max = Math.max(...vals);
  const avg = vals.reduce((a,b)=>a+b,0)/vals.length;
  return {min, max, avg, u0: min/avg, lums, N, vals, indirect};
}

function buildLux(res){
  clearGroup(luxGroup);
  if(!S.showLux) return;
  const N = res.N, cw = S.W/N, cd = S.D/N;
  const g = new THREE.PlaneGeometry(cw*0.98, cd*0.98);
  const merged = [];
  for(let i=0;i<N;i++) for(let j=0;j<N;j++){
    const v = res.vals[i*N + j];
    const gg = g.clone();
    gg.rotateX(-Math.PI/2);
    gg.translate((i+0.5)*cw, WORK_H + 0.01, (j+0.5)*cd);
    // 200 lx (qırmızı) → 400 lx (sarı) → 700 lx (yaşıl)
    const t = Math.max(0, Math.min(1, (v - 200) / 500));
    const c = new THREE.Color().setHSL(t*0.33, 0.85, 0.48);
    const arr = new Float32Array(gg.attributes.position.count * 3);
    for(let k=0;k<gg.attributes.position.count;k++){ arr[k*3]=c.r; arr[k*3+1]=c.g; arr[k*3+2]=c.b; }
    gg.setAttribute('color', new THREE.BufferAttribute(arr, 3));
    merged.push(gg);
  }
  const all = THREE.BufferGeometryUtils.mergeBufferGeometries(merged, false);
  merged.forEach(x=>x.dispose());
  g.dispose();
  const mesh = new THREE.Mesh(all, new THREE.MeshBasicMaterial({
    vertexColors:true, transparent:true, opacity:0.55, side:THREE.DoubleSide, depthWrite:false
  }));
  luxGroup.add(mesh);
}

/* ══════════ PARAMETRİK MÜHƏNDİS ANALİZİ ══════════
   Bütün hesablar otağın cari ölçüsündən çıxarılır — En/Uz/Hün dəyişəndə
   nəticələr dərhal yenilənir.                                            */

/* Akustika — Sabine düsturu, 500 Hz. RT60 = 0,161·V / A               */
const CEIL_COVER = 0.70;    // akustik asma tavanın örtdüyü tavan payı
const WALL_PANEL = 12;      // divar panelinin sahəsi, m²
function analyseAcoustics(){
  const V = S.W * S.D * S.H;
  const Af = S.W * S.D;
  const wall = 2*(S.W + S.D)*S.H;
  const glass = 2*(1.30*1.90);
  const occ = Math.round(S.objects.reduce((s,o)=>s+o.def.seats,0) * 0.85) + 1;

  // oturmuş adam ≈ 0,40 sabin · mebel/PC ≈ 0,10 sabin
  const soft = occ*0.40 + S.objects.reduce((s,o)=>s+o.def.seats,0)*0.10;

  const ceilA = Af * CEIL_COVER;               // akustik tavanın sahəsi
  const bare = Af*0.03 + Af*0.05 + (wall-glass)*0.02 + glass*0.05 + soft;
  const withCeil = Af*0.03 + ceilA*0.85 + (Af-ceilA)*0.05 + (wall-glass)*0.02 + glass*0.05 + soft;
  const full = withCeil - (wall-glass)*0.02 + (wall-glass-WALL_PANEL)*0.02 + WALL_PANEL*0.75;

  return {
    rt_bare: 0.161*V/bare,
    rt_ceiling: 0.161*V/withCeil,
    rt_full: 0.161*V/full,
    limit: 0.60, V, occ,
    ceilArea: ceilA, wallPanel: WALL_PANEL
  };
}

/* Soyutma yükü — avadanlıq + insan + işıq + xarici qazanc */
function analyseCooling(){
  const seats = S.objects.reduce((s,o)=>s+o.def.seats,0);
  let eq = 0;
  S.objects.forEach(o=>{
    eq += ({pod:4*148, desk1:148, a11y:148, teacher:250, gpu:450,
            rack:800, nas:60, ups:120, printer:200, byod:0, iot:120})[o.type] || 0;
  });
  const light = ceilingGrid().cols * ceilingGrid().rows * 40;
  const occ = Math.round(seats*0.85) + 1;
  const people = occ * 75;
  const env = Math.round(S.W*S.D*13);          // pəncərə/qonşu otaqdan qazanc
  const total = eq + light + people + env;
  return {eq, light, people, env, total, btu: total*3.412, occ,
          units: Math.ceil(total*3.412/24000)};
}

/* Tahliyə — çıxış sayı, qapı eni, ən uzaq məsafə */
function analyseEgress(){
  const seats = S.objects.reduce((s,o)=>s+o.def.seats,0);
  const occ = Math.round(seats*0.85) + 1;
  return {
    occ,
    exitsNeeded: occ > 50 ? 2 : 1,
    doorWidth: 1.10,
    doorCapacity: Math.round(1.10/0.55*100),
    maxTravel: Math.hypot(S.W-1, S.D-1),
    travelLimit: 25
  };
}

/* Əlçatanlıq — Ø1,5 m manevr dairəsi boş olmalıdır */
function analyseA11y(){
  const stations = S.objects.filter(o=>o.def.a11y);
  const issues = [];
  stations.forEach(o=>{
    // manevr dairəsinin mərkəzi (istifadəçi tərəfi)
    const cx = o.x - Math.sin(o.rot)*0.85, cz = o.z - Math.cos(o.rot)*0.85;
    let blocked = false;
    S.objects.forEach(q=>{
      if(q === o || q.def.wall) return;
      const A = aabb(q);
      const dx = Math.max(A.x0 - cx, 0, cx - A.x1);
      const dz = Math.max(A.z0 - cz, 0, cz - A.z1);
      if(Math.hypot(dx, dz) < 0.75) blocked = true;
    });
    if(cx < 0.75 || cz < 0.75 || cx > S.W-0.75 || cz > S.D-0.75) blocked = true;
    if(blocked) issues.push(o);
  });
  return {count: stations.length, issues, need: Math.max(1, Math.round(
    S.objects.reduce((s,o)=>s+o.def.seats,0) / 20))};
}

/* Elektrik — rozetka/port sayı və ayrılmış xəttin gücü.
   Ayrılmış xətt "hesabi yükü 2-yə yuvarlaqlaşdırmaqla" deyil, standart nominal
   sıradan seçilir və üzərinə ən azı 15 % ehtiyat qoyulur: xətt bir dəfə çəkilir,
   sonradan artırmaq divarın sökülməsi deməkdir. */
const LINE_RATINGS = [10, 12, 16, 20, 25, 32, 40, 50, 63];   // kVt
const LINE_MARGIN  = 1.15;
function analyseElectric(){
  const seats = S.objects.reduce((s,o)=>s+o.def.seats, 0);
  const cool  = analyseCooling();
  const wsObjs = S.objects.filter(o=>o.def.seats > 0 || o.type === 'teacher' || o.type === 'gpu');
  const kwIT  = (cool.eq + cool.light)/1000;
  const kwAC  = cool.units * 2.2;
  const kwCalc = (kwIT + kwAC) * 1.25;
  const kwLine = LINE_RATINGS.find(r => r >= kwCalc*LINE_MARGIN) ||
                 Math.ceil(kwCalc*LINE_MARGIN);
  return {
    seats, cool, kwIT, kwAC, kwCalc, kwLine,
    sockets: seats*2 + wsObjs.length*2 + 8,
    rj45:    seats + 6
  };
}

/* Tövsiyə olunan minimum sahə.
   Sabit iş yerləri (pod, tək masa, əlçatan) tam norma ilə — 2,30 m²/yer.
   Çevik yerlər (BYOD, IoT skamyası) növbə ilə istifadə olunduğuna görə
   1,60 m²/yer. Əlçatan yerə manevr dairəsi üçün əlavə 1,20 m².            */
const FIXED_TYPES = ['pod','desk1','a11y','teacher','gpu'];
function recommendedArea(){
  let fixed = 0, flex = 0;
  S.objects.forEach(o=>{
    if(!o.def.seats) return;
    if(FIXED_TYPES.indexOf(o.type) >= 0) fixed += o.def.seats;
    else flex += o.def.seats;
  });
  const a11yN = S.objects.filter(o=>o.def.a11y).length;
  return fixed*2.30 + flex*1.60 + a11yN*1.20;
}

function renderTechPanels(){
  const res = analyseLux();
  const ok = res.avg >= 400 && res.u0 >= 0.6;
  const cls = v => v >= 400 ? 'ok' : v >= 300 ? 'warn' : 'err';
  document.getElementById('luxbox').innerHTML = `
    <div class="stat"><span class="k">Orta işıqlanma</span>
      <span class="v ${cls(res.avg)}">${Math.round(res.avg)} lx</span></div>
    <div class="stat"><span class="k">Minimum</span>
      <span class="v ${cls(res.min)}">${Math.round(res.min)} lx</span></div>
    <div class="stat"><span class="k">Bərabərlik U₀</span>
      <span class="v ${res.u0>=0.6?'ok':'warn'}">${res.u0.toFixed(2)}</span></div>
    <div class="stat"><span class="k">Panel sayı</span><span class="v">${res.lums.length} × ${LUM_FLUX} lm</span></div>
    <div class="msg ${ok?'ok':'warn'}" style="margin-top:6px">
      ${ok ? 'Norma ödənir: ≥400 lx və U₀ ≥ 0,60'
           : `Tələb: ≥400 lx, U₀ ≥ 0,60 — ${res.avg<400?'panel sayı və ya gücü artırılmalıdır':'paylanma qeyri-bərabərdir'}`}
    </div>
    <div class="empty" style="font-style:normal;font-size:10px;line-height:1.45">
      Model: Lambert paylanmalı tavan panelləri (birbaşa) + lümen metodu ilə əks olunan
      komponent ${Math.round(res.indirect)} lx. İş səthi 0,75 m, istismar əmsalı ${MAINT}.
      Təxmini hesabdır — icra layihəsi üçün DIALux ilə dəqiqləşdirilməlidir.
    </div>`;
  buildLux(res);

  // ── Akustika ──
  const ac = analyseAcoustics();
  const acOk = ac.rt_bare <= ac.limit;
  document.getElementById('acou').innerHTML = `
    <div class="stat"><span class="k">Həcm</span><span class="v">${ac.V.toFixed(0)} m³</span></div>
    <div class="stat"><span class="k">RT60 — işlənməmiş</span>
      <span class="v ${acOk?'ok':'err'}">${ac.rt_bare.toFixed(2)} s</span></div>
    <div class="stat"><span class="k">Akustik tavanla</span>
      <span class="v ${ac.rt_ceiling<=ac.limit?'ok':'warn'}">${ac.rt_ceiling.toFixed(2)} s</span></div>
    <div class="stat"><span class="k">Tavan + divar paneli</span>
      <span class="v ok">${ac.rt_full.toFixed(2)} s</span></div>
    <div class="msg ${acOk?'ok':'err'}" style="margin-top:6px">
      ${acOk ? 'Norma ödənir (≤ 0,60 s)'
             : `Norma pozulur: ${ac.rt_bare.toFixed(2)} s > 0,60 s — müəllimin nitqi anlaşılmır.
                Akustik asma tavan (≈${ac.ceilArea.toFixed(0)} m², tavanın ${(CEIL_COVER*100).toFixed(0)} %-i)
                problemi həll edir.
                <b>Büdcəyə daxil edilməyib</b> — ayrıca qərar tələb olunur.`}
    </div>`;

  // ── Əlçatanlıq ──
  const a11 = analyseA11y();
  const a11Ok = a11.count >= a11.need && a11.issues.length === 0;
  document.getElementById('a11y').innerHTML = `
    <div class="stat"><span class="k">Əlçatan iş yeri</span>
      <span class="v ${a11.count>=a11.need?'ok':'err'}">${a11.count} / ${a11.need} tələb</span></div>
    <div class="stat"><span class="k">Manevr dairəsi Ø1,5 m</span>
      <span class="v ${a11.issues.length?'err':'ok'}">${a11.issues.length ? a11.issues.length+' pozuntu' : 'sərbəst'}</span></div>
    <div class="msg ${a11Ok?'ok':'warn'}" style="margin-top:6px">
      ${a11Ok ? 'Masa hündürlüyü 70–120 sm tənzimlənir, yanaşma sərbəstdir'
              : a11.count < a11.need
                ? `Hər 20 iş yerinə 1 əlçatan yer tövsiyə olunur — ${a11.need - a11.count} ədəd çatmır`
                : 'Manevr dairəsi başqa mebellə kəsişir — əlçatan yeri sərbəst sahəyə köçürün'}
    </div>`;

  // ── Elektrik və iqlim ──
  const el = analyseElectric();
  const {cool, kwIT, kwCalc, kwLine, sockets, rj45} = el;
  const eg = analyseEgress();
  document.getElementById('elec').innerHTML = [
    ['Elektrik rozetkası', sockets + ' ədəd'],
    ['Şəbəkə portu (RJ-45)', rj45 + ' ədəd'],
    ['İT avadanlığı + işıq', kwIT.toFixed(1) + ' kVt'],
    ['Hesabi yük (k=1,25)', kwCalc.toFixed(1) + ' kVt'],
    ['Tövsiyə olunan xətt', kwLine + ' kVt'],
    ['Soyutma yükü', Math.round(cool.btu).toLocaleString('az-AZ').replace(/,/g,' ') + ' BTU/s'],
    ['Kondisioner', cool.units + ' × 24000 BTU'],
    ['Tahliyə', `${eg.occ} nəfər / ${eg.exitsNeeded} çıxış`],
    ['Ən uzaq tahliyə yolu', `${eg.maxTravel.toFixed(1)} m (norma ≤${eg.travelLimit} m)`],
    ['Qapı buraxma qabiliyyəti', `${eg.doorCapacity} nəfər (${eg.doorWidth.toFixed(2)} m)`]
  ].map(r=>`<div class="stat"><span class="k">${r[0]}</span><span class="v">${r[1]}</span></div>`).join('');

  // ── Otaq ölçüsü tövsiyəsi ──
  const need = recommendedArea();
  const have = S.W * S.D;
  const hint = document.getElementById('sizehint');
  if(hint) hint.innerHTML =
    `Cari sahə <b>${have.toFixed(1)} m²</b> · tələb olunan minimum
     <b class="${have>=need?'':'v err'}">${need.toFixed(1)} m²</b><br>
     ${have >= need
       ? '<span style="color:#2ecc71">Sahə kifayətdir.</span>'
       : `<span style="color:#e74c3c">${(need-have).toFixed(1)} m² çatmır</span> —
          En ${(need/S.D).toFixed(1)} m və ya Uz ${(need/S.W).toFixed(1)} m olmalıdır.`}`;
}

/* ══════════════════════════════════════════════════════════════════
   PARAMETR İXRACI — vahid həqiqət mənbəyi
   Bütün mühəndis göstəriciləri burada, tək yerdə hesablanır və
   lab_parametrleri.json faylına yazılır. sened_qur.py və sxem_qur.py
   həmin faylı oxuyur — beləliklə PDF, sxemlər və 3D model heç vaxt
   bir-birindən ayrı düşmür.
   ══════════════════════════════════════════════════════════════════ */
/* Düzülüş — ölçü, rəng və mövqe ilə birlikdə.
   Plan sxemi (sxem_qur.py) məhz bu məlumatdan çəkilir, ona görə 3D modeldə
   nə varsa, 2D planda da eyni yerdə olur. */
function layoutJSON(){
  return {
    otaq:{en:S.W, uzunluq:S.D, hundurluk:S.H, sahe:+(S.W*S.D).toFixed(2)},
    is_yeri: S.objects.reduce((s,o)=> s+o.def.seats, 0),
    budce_azn: S.objects.reduce((s,o)=> s+o.def.price, 0),
    obyektler: S.objects.map(o=>({
      tip:o.type, ad:o.def.nm,
      x:+o.x.toFixed(2), z:+o.z.toFixed(2), bucaq:Math.round(o.rot*180/Math.PI),
      en:o.def.w, uzunluq:o.def.d,
      reng:'#' + o.def.col.toString(16).padStart(6,'0'),
      is_yeri:o.def.seats, divar:!!o.def.wall, avadanliq:!!o.def.equip,
      qiymet:o.def.price
    }))
  };
}

function paramsJSON(){
  const r2 = v => +v.toFixed(2);
  const lux  = analyseLux();
  const ac   = analyseAcoustics();
  const el   = analyseElectric();
  const cool = el.cool;
  const eg   = analyseEgress();
  const a11  = analyseA11y();

  const seats = el.seats;
  let fixedSeats = 0, flexSeats = 0;
  S.objects.forEach(o=>{
    if(!o.def.seats) return;
    if(FIXED_TYPES.indexOf(o.type) >= 0) fixedSeats += o.def.seats;
    else flexSeats += o.def.seats;
  });
  const say = t => S.objects.filter(o => o.type === t).length;

  return {
    versiya: 1,
    menbe: '3D Dizayner (3d/app.js) — avtomatik ixrac',
    otaq: {en:S.W, uzunluq:S.D, hundurluk:S.H, sahe:r2(S.W*S.D)},
    tutum: {
      is_yeri: seats, sabit: fixedSeats, cevik: flexSeats,
      elcatan: a11.count, eyni_anda: cool.occ,
      min_sahe: r2(recommendedArea()),
      sixliq: seats ? r2(S.W*S.D/seats) : 0
    },
    say: {
      pod:say('pod'), a11y:say('a11y'), teacher:say('teacher'), gpu:say('gpu'),
      byod:say('byod'), iot:say('iot'), rack:say('rack'), ups:say('ups'),
      nas:say('nas'), printer:say('printer'), cabinet:say('cabinet'),
      panel:say('panel'), screen55:say('screen55'), ac:say('ac'), desk1:say('desk1'),
      // stul: pod + BYOD + müəllim (əlçatan yerdə əlil arabası oturur),
      // taburet: IoT skamyası
      stul: say('pod')*4 + say('byod')*6 + say('teacher') + say('desk1') + say('gpu'),
      taburet: say('iot')*6,
      monitor_telebe: say('pod')*4 + say('desk1')
    },
    isiqlanma: {
      orta: Math.round(lux.avg), min: Math.round(lux.min), maks: Math.round(lux.max),
      u0: r2(lux.u0), panel_sayi: lux.lums.length, panel_lm: LUM_FLUX,
      istismar_emsali: MAINT, is_sethi_h: WORK_H,
      eks_komponent: Math.round(lux.indirect), norma: 400, u0_norma: 0.60
    },
    akustika: {
      hecm: r2(ac.V),
      rt_bare: r2(ac.rt_bare), rt_ceiling: r2(ac.rt_ceiling), rt_full: r2(ac.rt_full),
      limit: ac.limit, tavan_sahesi: r2(ac.ceilArea), divar_paneli: ac.wallPanel,
      ortuk_payi: CEIL_COVER
    },
    soyutma: {
      avadanliq_vt: cool.eq, isiq_vt: cool.light, insan_vt: cool.people,
      xarici_vt: cool.env, cem_vt: cool.total,
      btu: Math.round(cool.btu), kondisioner: cool.units, kondisioner_btu: 24000
    },
    elektrik: {
      kw_it: r2(el.kwIT), kw_kondisioner: r2(el.kwAC),
      kw_hesabi: r2(el.kwCalc), kw_xett: el.kwLine,
      emsal: 1.25, ehtiyat: LINE_MARGIN,
      rozetka: el.sockets, rj45: el.rj45
    },
    tahliye: {
      nefer: eg.occ, cixis: eg.exitsNeeded, qapi_eni: eg.doorWidth,
      qapi_tutumu: eg.doorCapacity,
      en_uzaq_m: r2(eg.maxTravel), limit_m: eg.travelLimit
    },
    elcatanliq: {say: a11.count, teleb: a11.need, pozuntu: a11.issues.length},
    duzulus: layoutJSON()
  };
}

/* ---------- Kamera presetləri ---------- */
const PRESETS = {
  corner:  ()=> ({p:[S.W*1.05, S.D*0.95, S.D*1.55], t:[S.W/2, 0.9, S.D/2]}),
  teacher: ()=> ({p:[S.W*0.82, 1.62, S.D-0.75],     t:[S.W*0.42, 1.15, S.D*0.35]}),
  student: ()=> ({p:[S.W*0.16, 1.24, S.D*0.30],     t:[S.W*0.55, 1.35, S.D-0.4]}),
  door:    ()=> ({p:[S.W*0.66, 1.65, 0.7],          t:[S.W*0.40, 1.20, S.D*0.75]}),
  server:  ()=> ({p:[S.W*0.30, 1.70, S.D*0.72],     t:[0.9, 1.20, S.D-0.35]})
};
function applyPreset(k){
  const P = PRESETS[k]; if(!P) return;
  const v = P();
  setMode('3d');
  camera.position.set(v.p[0], v.p[1], v.p[2]);
  controls.target.set(v.t[0], v.t[1], v.t[2]);
  controls.update();
}

/* ---------- 4K render ----------
   Zəif GPU-da 3840 px SSAO/SMAA buferləri yaddaşa sığmaya bilər və kontekst
   itir. Ona görə hədəf en aparatın icazə verdiyi maksimuma görə kiçildilir,
   render try/catch içindədir və hər halda ilkin ölçü bərpa olunur.          */
function render4K(){
  const el = renderer.domElement;
  const ow = el.clientWidth, oh = el.clientHeight, odpr = renderer.getPixelRatio();
  const gl = renderer.getContext();
  const cap = Math.min(gl.getParameter(gl.MAX_TEXTURE_SIZE),
                       gl.getParameter(gl.MAX_RENDERBUFFER_SIZE));
  const W4 = Math.min(3840, cap);
  const H4 = Math.min(Math.round(W4 * oh / ow), cap);

  const restore = ()=>{
    renderer.setPixelRatio(odpr);
    renderer.setSize(ow, oh, false);
    camera.aspect = ow/oh; camera.updateProjectionMatrix();
    if(composer){
      composer.setSize(ow, oh);
      if(ssaoPass) ssaoPass.setSize(ow, oh);
      if(smaaPass) smaaPass.setSize(ow*odpr, oh*odpr);
    }
  };

  try{
    renderer.setPixelRatio(1);
    renderer.setSize(W4, H4, false);
    camera.aspect = W4/H4; camera.updateProjectionMatrix();
    if(composer){
      composer.setSize(W4, H4);
      if(ssaoPass) ssaoPass.setSize(W4, H4);
      if(smaaPass) smaaPass.setSize(W4, H4);
    }
    renderFrame();
  }catch(err){
    restore();
    alert('Yüksək ayırdetmə ilə render alınmadı (qrafik yaddaşı çatmır).\n' +
          'Adi "PNG" düyməsindən istifadə edin.\n\n' + err.message);
    return;
  }

  el.toBlob(b=>{
    if(b) dl(b, `laboratoriya-${W4}x${H4}.png`);
    restore();
  }, 'image/png');
}

/* ------------------------------------------------------------------ REJİMLƏR */
const walk = {yaw:-Math.PI/2, pitch:-0.05, keys:{}, look:false};

/* Otağı istənilən pəncərə nisbətində tam kadra salır.
   Sferik təxmin əvəzinə otağın 8 küncü proyeksiya olunur və məsafə
   ekranın ~88 %-ni dolduracaq həddə qədər tənzimlənir.                */
function frameRoom(keepDir){
  const t = new THREE.Vector3(S.W/2, 1.0, S.D/2);

  let dir;
  if(S.mode === 'top') dir = new THREE.Vector3(0, 1, 0.0001).normalize();
  else if(keepDir && camera.position.distanceTo(controls.target) > 0.1)
    dir = camera.position.clone().sub(controls.target).normalize();
  else dir = new THREE.Vector3(0.80, 0.62, 1.05).normalize();

  const pts = [];
  for(const x of [0, S.W])
    for(const y of [0, S.H])
      for(const z of [0, S.D]) pts.push(new THREE.Vector3(x, y, z));

  let dist = Math.max(S.W, S.D) * 1.3;
  for(let i = 0; i < 40; i++){
    camera.position.copy(t).add(dir.clone().multiplyScalar(dist));
    camera.lookAt(t);
    camera.updateMatrixWorld(true);
    let m = 0;
    for(const p of pts){
      const v = p.clone().project(camera);
      m = Math.max(m, Math.abs(v.x), Math.abs(v.y));
    }
    if(m > 0.94)      dist *= 1.05;
    else if(m < 0.82) dist *= 0.965;
    else break;
  }

  controls.target.copy(t);
  controls.maxDistance = dist * 2.4;
  controls.minDistance = Math.min(2, dist * 0.15);
  controls.update();
}

function setMode(m){
  S.mode = m;
  ['v3d','vtop','vwalk'].forEach((id,i)=>
    $(id).classList.toggle('on', ['3d','top','walk'][i] === m));

  const ceil = roomGroup.getObjectByName('ceiling');
  if(ceil) ceil.visible = (m === 'walk') && S.showWalls;

  if(m === 'walk'){
    controls.enabled = false;
    select(null);
    camera.position.set(S.W/2, 1.6, 1.2);
    walk.yaw = -Math.PI/2; walk.pitch = -0.05;
    renderer.domElement.style.cursor = 'move';
  }else{
    controls.enabled = true;
    renderer.domElement.style.cursor = 'default';
    controls.enableRotate = (m !== 'top');
    frameRoom(false);
  }
}
$('v3d').onclick  = ()=> setMode('3d');
$('vtop').onclick = ()=> setMode('top');
$('vwalk').onclick= ()=> setMode('walk');

/* Sahələrdə yazarkən W/A/S/D gəzinti hərəkəti kimi qəbul edilməməlidir.
   Pəncərə fokusu itəndə basılı qalan düymələr də təmizlənir. */
const typing = e => /^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName);
addEventListener('keydown', e=>{ if(!typing(e)) walk.keys[e.key.toLowerCase()] = true; });
addEventListener('keyup',   e=>{ walk.keys[e.key.toLowerCase()] = false; });
addEventListener('blur',    ()=>{ walk.keys = {}; walk.look = false; });
renderer.domElement.addEventListener('pointerdown', e=>{ if(S.mode==='walk') walk.look = true; });
addEventListener('pointerup', ()=> walk.look = false);
renderer.domElement.addEventListener('pointermove', e=>{
  if(S.mode !== 'walk' || !walk.look) return;
  walk.yaw   -= e.movementX * 0.0032;
  walk.pitch -= e.movementY * 0.0032;
  walk.pitch  = Math.max(-1.2, Math.min(1.2, walk.pitch));
});

function stepWalk(dt){
  const sp = (walk.keys['shift'] ? 3.6 : 1.9) * dt;
  let fx = 0, fz = 0;
  if(walk.keys['w'] || walk.keys['arrowup'])    fz += 1;
  if(walk.keys['s'] || walk.keys['arrowdown'])  fz -= 1;
  if(walk.keys['a'] || walk.keys['arrowleft'])  fx -= 1;
  if(walk.keys['d'] || walk.keys['arrowright']) fx += 1;

  const sin = Math.sin(walk.yaw), cos = Math.cos(walk.yaw);
  camera.position.x += (cos*fz + -sin*fx) * sp;
  camera.position.z += (sin*fz +  cos*fx) * sp;
  camera.position.x = Math.min(Math.max(camera.position.x, 0.35), S.W - 0.35);
  camera.position.z = Math.min(Math.max(camera.position.z, 0.35), S.D - 0.35);
  camera.position.y = 1.6;

  camera.lookAt(
    camera.position.x + Math.cos(walk.yaw) * Math.cos(walk.pitch),
    camera.position.y + Math.sin(walk.pitch),
    camera.position.z + Math.sin(walk.yaw) * Math.cos(walk.pitch)
  );
}

/* ------------------------------------------------------------------ POST-EMAL
   Render → SSAO (təmas kölgələri) → Bloom (ekran işıqları)
        → Qamma korreksiyası → SMAA (kənar hamarlaması)                       */
let composer, ssaoPass, bloomPass, smaaPass;

function buildComposer(w, h){
  const dpr = renderer.getPixelRatio();
  composer = new THREE.EffectComposer(renderer);
  composer.setSize(w, h);

  composer.addPass(new THREE.RenderPass(scene, camera));

  // SSAO ən bahalı keçiddir (ölçüldü: 265 → 69 FPS). Kiçik və orta ekranlarda
  // 32 nümunə saxlanılır; çox böyük kanvasda 16-ya enir ki, rəvanlıq itməsin.
  const kernel = (w * h > 1600000) ? 16 : 32;
  ssaoPass = new THREE.SSAOPass(scene, camera, w, h, kernel);
  // Dəyərlər AO buferi ölçülərək kalibrlənib: mebel miqyasında ən güclü
  // təmas kölgəsi 0,6 m radiusda alınır (daha kiçik radius demək olar təsirsizdir).
  ssaoPass.kernelRadius = 0.60;      // metrlə
  ssaoPass.minDistance  = 0.002;
  ssaoPass.maxDistance  = 0.30;
  composer.addPass(ssaoPass);

  bloomPass = new THREE.UnrealBloomPass(new THREE.Vector2(w, h), 0.24, 0.62, 0.90);
  composer.addPass(bloomPass);

  composer.addPass(new THREE.ShaderPass(THREE.GammaCorrectionShader));

  smaaPass = new THREE.SMAAPass(w * dpr, h * dpr);
  composer.addPass(smaaPass);
}

/* ------------------------------------------------------------------ DÖVR */
function resize(){
  const w = view.clientWidth, h = view.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w/h;
  camera.updateProjectionMatrix();
  if(composer){
    composer.setSize(w, h);
    if(ssaoPass) ssaoPass.setSize(w, h);
    if(smaaPass) smaaPass.setSize(w * renderer.getPixelRatio(), h * renderer.getPixelRatio());
  }
  if(S.mode !== 'walk') frameRoom(true);   // baxış bucağı qorunur, məsafə uyğunlaşır
}
addEventListener('resize', resize);

/* Kameraya yaxın divarları gizlədir — otağın içi həmişə görünür qalır */
function cullWalls(){
  const w = roomGroup.getObjectByName('walls');
  if(!w) return;
  const inside = S.mode === 'walk';
  const p = camera.position;
  const vis = {
    z0: inside || p.z >= 0,
    zD: inside || p.z <= S.D,
    x0: inside || p.x >= 0,
    xW: inside || p.x <= S.W
  };
  Object.keys(vis).forEach(k=>{
    const g = w.getObjectByName('side_'+k);
    if(g) g.visible = S.showWalls && vis[k];
  });
}

let last = performance.now();
(function loop(now){
  requestAnimationFrame(loop);
  const dt = Math.min((now - last)/1000, 0.1); last = now;
  if(S.mode === 'walk') stepWalk(dt);
  else controls.update();
  cullWalls();
  if(composer) composer.render(dt);
  else renderer.render(scene, camera);
})(last);

/* ------------------------------------------------------------------ BAŞLAT */
loadEnvironment(function(){
  try{
    buildRoom();
    const w = view.clientWidth || 800, h = view.clientHeight || 600;
    renderer.setSize(w, h, false);
    camera.aspect = w/h; camera.updateProjectionMatrix();
    buildComposer(w, h);

    if(!restore()) loadLayout(DEFAULT_LAYOUT.map(o=>({t:o.t,x:o.x,z:o.z,r:o.r||0})),
                              DEFAULT_ROOM.W, DEFAULT_ROOM.D, true, DEFAULT_ROOM.H);
    setMode('3d');
    refresh();
  }catch(err){
    // Səhnə qurulmadısa istifadəçi "yüklənir…" ekranında qalmamalıdır
    fatal('Səhnə qurulmadı: ' + err.message);
  }
  const ld = document.getElementById('loading');
  if(ld) ld.remove();
});
