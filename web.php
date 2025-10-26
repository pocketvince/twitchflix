<?php
function esc($s){ return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function truncate_title($s,$m=60){ return (mb_strlen($s,'UTF-8')>$m)?rtrim(mb_substr($s,0,$m,'UTF-8')).",...":$s; }
function format_duration($tw){
  if(!$tw) return "";
  preg_match_all('/(\d+)\s*([hms])/i', $tw, $parts, PREG_SET_ORDER);
  if(!$parts) return "";
  $H=$M=$S=0;
  foreach($parts as $p){
    $v=(int)$p[1];
    switch(strtolower($p[2])){
      case 'h': $H += $v; break;
      case 'm': $M += $v; break;
      case 's': $S += $v; break;
    }
  }
  $t = $H*3600 + $M*60 + $S;
  if($t <= 0) return "";
  $H = intdiv($t, 3600);
  $M = intdiv($t % 3600, 60);
  $S = $t % 60;
  return $H ? sprintf("%d:%02d:%02d", $H, $M, $S) : sprintf("%d:%02d", $M, $S);
}

function flag_for_lang($l){$m=['fr'=>'🇫🇷','en'=>'🇬🇧','en-gb'=>'🇬🇧','en-us'=>'🇺🇸','de'=>'🇩🇪','es'=>'🇪🇸','pt'=>'🇵🇹','pt-br'=>'🇧🇷','it'=>'🇮🇹','nl'=>'🇳🇱','ru'=>'🇷🇺','ja'=>'🇯🇵','ko'=>'🇰🇷','zh'=>'🇨🇳','tr'=>'🇹🇷','pl'=>'🇵🇱','sv'=>'🇸🇪','no'=>'🇳🇴','da'=>'🇩🇰','fi'=>'🇫🇮'];$l=strtolower($l??'');return $m[$l]??strtoupper($l);}
function parse_iso($s){try{return new DateTimeImmutable($s);}catch(Exception){return null;}}
function is_new($d){if(!$d)return 0;$t=new DateTimeImmutable('today',new DateTimeZone('Europe/Brussels'));$y=$t->sub(new DateInterval('P1D'));$d=$d->setTime(0,0,0);return($d==$t||$d==$y);}
function fdate($d){return$d?$d->setTimezone(new DateTimeZone('Europe/Brussels'))->format('d M Y • H:i'):"";}
function first($a,$k){foreach($a as$x){if(!empty($x[$k]))return$x[$k];}return null;}

$f='videos.json';if(!is_file($f)){echo"videos.json missing";exit;}
$j=json_decode(file_get_contents($f),true)?:[];
$g=[];foreach($j as$v){$g[$v['login']??''][]=$v;}
ksort($g);foreach($g as&$a){usort($a,fn($x,$y)=>strtotime($y['created_at'])<=>strtotime($x['created_at']));}unset($a);
?>
<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport"content="width=device-width,initial-scale=1"><title>Twitchflix</title>
<style>
:root{--bg:#171720;--card:#1b1c27;--text:#f1f3f5;--muted:#aab0b9;--accent:#9146FF;--new:#00d084;--shadow:0 8px 24px rgba(0,0,0,.35);}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,sans-serif}

a{color:inherit;text-decoration:none}
a:hover{text-decoration:underline;text-underline-offset:2px}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:8px}

.container{max-width:1200px;margin:0 auto;padding:20px}
.header{position:sticky;top:0;background:rgba(23,23,32,.9);backdrop-filter:blur(8px);z-index:10}
.title{font-weight:900;font-size:22px;padding:16px 20px;color:#fff;background:linear-gradient(135deg,var(--accent),#b18aff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}

.section{margin:26px 4px 8px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(140px,1fr))}

.card{border-radius:16px;overflow:hidden;transition:transform .15s ease;cursor:pointer}
.card:hover{transform:translateY(-2px)}
.thumb{position:relative;aspect-ratio:2/3;border-radius:14px;overflow:hidden;background:var(--card);box-shadow:var(--shadow)}
.thumb img{width:100%;height:100%;object-fit:cover}
.badge{position:absolute;padding:6px 8px;border-radius:10px;font-size:12px;line-height:1;background:rgba(0,0,0,.55);color:#fff}
.badge-lang{top:8px;left:8px}
.badge-new{top:8px;right:8px;background:linear-gradient(135deg,var(--new),#31ffa6);color:#102018;font-weight:700}
.badge-duration{right:8px;bottom:8px;background:rgba(0,0,0,.65)}
.meta{padding:8px 4px 0}
.title-txt{font-size:14px;font-weight:600;line-height:1.3;margin:6px 2px 2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.date{font-size:12px;color:var(--muted);margin:0 2px 10px}

.profile-card{display:flex;align-items:center;flex-direction:column;gap:10px;padding:14px;border-radius:14px;background:#191a26;box-shadow:var(--shadow);border:1px solid rgba(255,255,255,.05)}
.profile-card img{width:72px;height:72px;border-radius:50%;object-fit:cover;background:#2b2d3b;box-shadow:0 4px 16px rgba(0,0,0,.35)}
.profile-card .visit{margin-top:4px;font-size:13px;color:#d9def5;border-bottom:1px dotted rgba(145,70,255,.6)}
</style>
<body>
<div class="header"><div class="title">Twitchflix</div></div>

<div class="container">
<?php foreach($g as$l=>$it):
  $pp=first($it,'profile_image_url');$ch=mb_strtoupper(mb_substr($l,0,1));?>
  <section class="section" id="<?=esc($l)?>">
    <div class="grid">
      <div class="profile-card">
        <?php if($pp):?><img src="<?=esc($pp)?>" alt="">
        <?php else:?><div style="width:72px;height:72px;display:grid;place-items:center;background:#2b2d3b;border-radius:50%;color:#ccc;font-weight:900"><?=$ch?></div><?php endif;?>
        <div style="font-weight:800">@<?=esc($l)?></div>
        <a class="visit" href="https://www.twitch.tv/<?=esc($l)?>" target="_blank" rel="noopener">Voir la chaîne ↗</a>
      </div>

      <?php foreach($it as$v):
        $url=$v['url']??'#';$img=$v['thumbnail_url']??'';$title=$v['title']??'';
        $lang=$v['language']??'';$dur=$v['duration']??'';$dt=parse_iso($v['created_at']??'');
        $flag=flag_for_lang($lang);$durF=format_duration($dur);$new=is_new($dt);
        $date=fdate($dt);$ts=truncate_title($title,72);?>
        <a href="<?=esc($url)?>" target="_blank" rel="noopener" class="card">
          <div class="thumb">
            <?php if($img):?><img src="<?=esc($img)?>" loading="lazy" alt="<?=esc($title)?>"><?php endif;?>
            <?php if($flag):?><span class="badge badge-lang"><?=$flag?></span><?php endif;?>
            <?php if($new):?><span class="badge badge-new">NEW</span><?php endif;?>
            <?php if($durF):?><span class="badge badge-duration"><?=esc($durF)?></span><?php endif;?>
          </div>
          <div class="meta">
            <div class="title-txt"><?=esc($ts)?></div>
            <div class="date"><?=esc($date)?></div>
          </div>
        </a>
      <?php endforeach;?>
    </div>
  </section>
<?php endforeach;?>
</div>
</body></html>
