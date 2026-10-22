"use strict";
const words={en:{title:"Your household, at a glance.",connect:"Connect to your kitchen",username:"Username",password:"Password",token:"Container setup token",household:"Household name",timezone:"Time zone",continue:"Continue",overview:"Kitchen overview",logout:"Sign out",jobs:"Recent background jobs",refresh:"Refresh",export:"Export household data",limitations:"Configure optional integrations through the server API or environment. Live compatibility must be verified.",ready:"Ready",error:"Request failed. Code: ",empty:"No background jobs yet.",pending:"Pending jobs",recipes:"Recipes",bring:"Bring!",disabled:"Not configured",configured:"Configured",verification:"Verification required"},de:{title:"Dein Haushalt auf einen Blick.",connect:"Mit deiner Küche verbinden",username:"Benutzername",password:"Passwort",token:"Einrichtungstoken des Containers",household:"Name des Haushalts",timezone:"Zeitzone",continue:"Weiter",overview:"Küchenübersicht",logout:"Abmelden",jobs:"Letzte Hintergrundaufträge",refresh:"Aktualisieren",export:"Haushaltsdaten exportieren",limitations:"Optionale Integrationen werden über die Server-API oder Umgebung eingerichtet. Die Live-Kompatibilität muss geprüft werden.",ready:"Bereit",error:"Anfrage fehlgeschlagen. Code: ",empty:"Noch keine Hintergrundaufträge.",pending:"Ausstehende Aufträge",recipes:"Rezepte",bring:"Bring!",disabled:"Nicht konfiguriert",configured:"Eingerichtet",verification:"Prüfung erforderlich"}};
const additions={"en": {"household_settings": "Household settings", "security": "Account and devices", "save": "Save changes", "default_language": "Default language", "current_password": "Current password", "new_password": "New password (at least 12 characters)", "change_password": "Change password and sign out all devices", "password_hint": "Every device must sign in again after a password change.", "sessions": "Device sessions", "revoke": "Revoke session", "revoke_question": "Revoke this device session?", "active": "Active", "revoked": "Revoked", "expires": "Refresh access expires", "ai_settings": "Optional AI extraction", "ai_enable": "Enable AI extraction", "provider": "Provider", "base_url": "API base URL", "model": "Model identifier", "api_key": "API key", "key_hint": "Leave blank to keep a saved key. Changing provider or URL clears the previous key unless you enter a new one.", "clear_key": "Remove saved key", "key_saved": "A key is stored securely. Its value is never shown here.", "no_key": "No API key stored.", "timeout": "Timeout in seconds", "content_limit": "Maximum source bytes", "request_limit": "AI requests per hour", "structured": "Use structured output when supported by this model", "local_http": "Allow HTTP for a trusted self-hosted AI endpoint", "ai_disclosure": "AI is optional. Source content is sent to the configured provider only with consent for that import. Keys stay on your server.", "ai_test": "Test saved AI configuration", "ai_test_hint": "Sends a small synthetic recipe, not household content. Provider usage charges may apply.", "ai_validated": "The provider returned a validated recipe for the connection test.", "bring_settings": "Bring! connection", "bring_email": "Bring! account email", "bring_password": "Bring! password", "bring_save": "Save Bring! credentials", "bring_test": "Connect and load existing lists", "bring_list": "Existing shopping list", "bring_select": "Use this list", "bring_retry": "Queue reconciliation", "disconnect": "Disconnect Bring!", "disconnect_question": "Remove the saved Bring! connection? Existing Bring! items will be preserved.", "bring_warning": "This unofficial integration requires a dedicated-list compatibility report before automatic writes are enabled. Saving credentials does not prove that authentication or sync works.", "bring_saved": "Credentials saved. Use Connect to verify access.", "bring_selected": "List selected. Automatic writes still require compatibility verification.", "queued": "Reconciliation queued; external changes are pending.", "data_management": "Data export and import", "archive_file": "Household JSON or ZIP export", "import_data": "Merge household export", "import_hint": "Imports merge atomically. Duplicate IDs reject the entire import; existing records are never overwritten. Keep a backup before importing.", "import_question": "Merge this export into the current household?", "saved": "Changes saved.", "imported": "Household data imported.", "busy": "Working…", "session_ended": "Sign in to continue. Your session may have expired or been revoked.", "limitations": "External integrations remain unverified until tested with your own configuration.", "storage": "Storage", "database": "Database", "photo_storage": "Recipe photos", "free_space": "Free on data volume", "current_session": "This session", "not_configured": "Not configured", "compatibility_unverified": "Compatibility verification required", "job_queued": "Queued", "job_running": "Running", "job_done": "Done", "job_failed": "Failed"}, "de": {"household_settings": "Haushaltseinstellungen", "security": "Konto und Geräte", "save": "Änderungen speichern", "default_language": "Standardsprache", "current_password": "Aktuelles Passwort", "new_password": "Neues Passwort (mindestens 12 Zeichen)", "change_password": "Passwort ändern und alle Geräte abmelden", "password_hint": "Nach einer Passwortänderung müssen sich alle Geräte erneut anmelden.", "sessions": "Gerätesitzungen", "revoke": "Sitzung widerrufen", "revoke_question": "Diese Gerätesitzung widerrufen?", "active": "Aktiv", "revoked": "Widerrufen", "expires": "Zugriff endet", "ai_settings": "Optionale KI-Extraktion", "ai_enable": "KI-Extraktion aktivieren", "provider": "Anbieter", "base_url": "API-Basis-URL", "model": "Modellkennung", "api_key": "API-Schlüssel", "key_hint": "Leer lassen, um einen gespeicherten Schlüssel beizubehalten. Beim Wechsel von Anbieter oder URL wird der bisherige Schlüssel entfernt, sofern du keinen neuen eingibst.", "clear_key": "Gespeicherten Schlüssel entfernen", "key_saved": "Ein Schlüssel ist sicher gespeichert. Sein Wert wird hier nicht angezeigt.", "no_key": "Kein API-Schlüssel gespeichert.", "timeout": "Zeitlimit in Sekunden", "content_limit": "Maximale Quellgröße in Bytes", "request_limit": "KI-Anfragen pro Stunde", "structured": "Strukturierte Ausgabe verwenden, wenn dieses Modell sie unterstützt", "local_http": "HTTP für einen vertrauenswürdigen selbst gehosteten KI-Endpunkt erlauben", "ai_disclosure": "KI ist optional. Quellinhalte werden nur mit Zustimmung für den jeweiligen Import an den konfigurierten Anbieter gesendet. Schlüssel bleiben auf deinem Server.", "ai_test": "Gespeicherte KI-Konfiguration testen", "ai_test_hint": "Sendet ein kleines künstliches Rezept, keine Haushaltsinhalte. Es können Nutzungskosten beim Anbieter entstehen.", "ai_validated": "Der Anbieter hat beim Verbindungstest ein gültiges Rezept zurückgegeben.", "bring_settings": "Bring!-Verbindung", "bring_email": "E-Mail des Bring!-Kontos", "bring_password": "Bring!-Passwort", "bring_save": "Bring!-Zugangsdaten speichern", "bring_test": "Verbinden und bestehende Listen laden", "bring_list": "Bestehende Einkaufsliste", "bring_select": "Diese Liste verwenden", "bring_retry": "Abgleich einreihen", "disconnect": "Bring! trennen", "disconnect_question": "Gespeicherte Bring!-Verbindung entfernen? Bestehende Bring!-Einträge bleiben erhalten.", "bring_warning": "Diese inoffizielle Integration benötigt einen Kompatibilitätsbericht einer eigenen Testliste, bevor automatische Schreibvorgänge aktiviert werden. Das Speichern von Zugangsdaten bestätigt weder die Anmeldung noch die Synchronisierung.", "bring_saved": "Zugangsdaten gespeichert. Prüfe den Zugriff mit Verbinden.", "bring_selected": "Liste gewählt. Automatische Schreibvorgänge benötigen weiterhin eine Kompatibilitätsprüfung.", "queued": "Abgleich eingereiht; externe Änderungen stehen aus.", "data_management": "Datenexport und Import", "archive_file": "JSON- oder ZIP-Haushaltsexport", "import_data": "Haushaltsexport zusammenführen", "import_hint": "Importe werden atomar zusammengeführt. Doppelte IDs führen zum Abbruch des gesamten Imports; vorhandene Einträge werden nicht überschrieben. Sichere deine Daten vor dem Import.", "import_question": "Diesen Export mit dem aktuellen Haushalt zusammenführen?", "saved": "Änderungen gespeichert.", "imported": "Haushaltsdaten importiert.", "busy": "Wird ausgeführt …", "session_ended": "Melde dich erneut an. Deine Sitzung ist möglicherweise abgelaufen oder wurde widerrufen.", "limitations": "Externe Integrationen sind erst nach einem Test mit deiner Konfiguration geprüft.", "storage": "Speicher", "database": "Datenbank", "photo_storage": "Rezeptfotos", "free_space": "Auf Datenvolume verfügbar", "current_session": "Diese Sitzung", "not_configured": "Nicht konfiguriert", "compatibility_unverified": "Kompatibilitätsprüfung erforderlich", "job_queued": "Eingereiht", "job_running": "Wird ausgeführt", "job_done": "Erledigt", "job_failed": "Fehlgeschlagen"}};
for(const language of ["en","de"]) Object.assign(words[language],additions[language]);
Object.assign(words.en, {title:"Household console",nav_overview:"Overview",nav_household:"Household",nav_security:"Account",nav_ai:"AI",nav_bring:"Bring!",nav_data:"Data",sidebar_note:"Your kitchen. Your server.",login_hint:"Connect to your household to manage this server and its integrations.",console_footer:"Independent open-source meal planning.",skip_content:"Skip to content",language:"Language"});
Object.assign(words.de, {title:"Haushaltsverwaltung",nav_overview:"Übersicht",nav_household:"Haushalt",nav_security:"Konto",nav_ai:"KI",nav_bring:"Bring!",nav_data:"Daten",sidebar_note:"Deine Küche. Dein Server.",login_hint:"Melde dich bei deinem Haushalt an, um den Server und seine Integrationen zu verwalten.",console_footer:"Unabhängige Open-Source-Essensplanung.",skip_content:"Zum Inhalt",language:"Sprache"});
Object.assign(words.en, {recent_imports:"Recent recipe imports",empty_imports:"No recipe imports yet.",kind_import:"Recipe import",kind_shopping:"Bring! reconciliation",kind_unknown:"Background task",job_preview:"Ready to review",job_needs_input:"Needs your input",job_confirmed:"Saved",job_cancelled:"Cancelled",job_unknown:"Status unavailable"});
Object.assign(words.de, {recent_imports:"Letzte Rezeptimporte",empty_imports:"Noch keine Rezeptimporte.",kind_import:"Rezeptimport",kind_shopping:"Bring!-Abgleich",kind_unknown:"Hintergrundauftrag",job_preview:"Bereit zur Prüfung",job_needs_input:"Deine Eingabe wird benötigt",job_confirmed:"Gespeichert",job_cancelled:"Abgebrochen",job_unknown:"Status nicht verfügbar"});
Object.assign(words.en, {diagnostic_code:"Diagnostic code: ",diagnostic_generic:"Could not complete. Review settings and try again.",diagnostic_rate_limit:"Request limit reached. Try again later.",diagnostic_auth:"Check the configured provider credentials.",diagnostic_bring_gate:"Verify the dedicated Bring! list before enabling automatic changes.",diagnostic_bring_list:"Select an available Bring! list in settings.",diagnostic_manual:"Paste the recipe text or enter it manually.",diagnostic_network:"Source could not be reached. Try again or paste its text.",diagnostic_invalid:"The source or provider did not return a valid recipe.",diagnostic_consent:"Allow this import to send content to the configured AI provider.",diagnostic_ai_config:"Configure an AI provider before using extraction."});
Object.assign(words.de, {diagnostic_code:"Diagnosecode: ",diagnostic_generic:"Nicht abgeschlossen. Prüfe die Einstellungen und versuche es erneut.",diagnostic_rate_limit:"Anfragelimit erreicht. Versuche es später erneut.",diagnostic_auth:"Prüfe die Zugangsdaten des konfigurierten Anbieters.",diagnostic_bring_gate:"Prüfe die eigene Bring!-Testliste, bevor automatische Änderungen aktiviert werden.",diagnostic_bring_list:"Wähle eine verfügbare Bring!-Liste in den Einstellungen.",diagnostic_manual:"Füge den Rezepttext ein oder gib das Rezept manuell ein.",diagnostic_network:"Quelle nicht erreichbar. Versuche es erneut oder füge den Text ein.",diagnostic_invalid:"Quelle oder Anbieter hat kein gültiges Rezept geliefert.",diagnostic_consent:"Erlaube für diesen Import die Übertragung an den konfigurierten KI-Anbieter.",diagnostic_ai_config:"Konfiguriere vor der Extraktion einen KI-Anbieter."});
Object.assign(words.en, {login_headline:"Get your hot buns in here.",setup_headline:"Set up your kitchen",login_joke:"Come for dinner. Stay for the buns.",peach_slap:"Slap the peach",setup_joke:"Good food starts here. Bad jokes are already included.",open_app:"Open meal planner",connect:"Your household account",console_footer:"Meal plans with benefits. Independently self-hosted.",sidebar_note:"Your kitchen. No strings attached."});
Object.assign(words.de, {login_headline:"Na, du heißes Früchtchen.",setup_headline:"Deine Küche einrichten",login_joke:"Komm zum Essen. Bleib für die heißen Backen.",peach_slap:"Dem Pfirsich einen Klaps geben",setup_joke:"Hier beginnt gutes Essen. Schlechte Witze sind inklusive.",open_app:"Essensplaner öffnen",connect:"Dein Haushaltskonto",console_footer:"Essensplanung mit gewissen Vorzügen. Unabhängig selbst gehostet.",sidebar_note:"Deine Küche. Ganz ohne Verpflichtungen."});
function diagnosticMessage(code){
  if(["ai_rate_limited","ai_request_limit"].includes(code))return words[locale].diagnostic_rate_limit;
  if(code==="ai_authentication_failed")return words[locale].diagnostic_auth;
  if(code==="bring_capability_unverified")return words[locale].diagnostic_bring_gate;
  if(["bring_list_not_selected","bring_list_not_found"].includes(code))return words[locale].diagnostic_bring_list;
  if(code==="ai_content_disclosure_consent_required")return words[locale].diagnostic_consent;
  if(code==="ai_not_configured")return words[locale].diagnostic_ai_config;
  if(["structured_recipe_not_found_use_manual_entry","source_unavailable_use_supplied_text","source_address_forbidden","source_url_forbidden"].includes(code))return words[locale].diagnostic_manual;
  if(["source_network_failed","source_dns_failed","source_timeout"].includes(code))return words[locale].diagnostic_network;
  if(["ai_invalid_response","ai_schema_validation_failed","invalid_extracted_recipe","ai_incomplete_recipe_review_manually"].includes(code))return words[locale].diagnostic_invalid;
  return words[locale].diagnostic_generic;
}
Object.assign(words.en, {theme:"Theme",theme_flo:"Flo · device",theme_dark:"After Dark · dark",theme_light:"Sunday · light",theme_not_saved:"Theme applied for this tab. Browser storage is unavailable; it may reset when you reopen."});
Object.assign(words.de, {theme:"Design",theme_flo:"Flo · Gerät",theme_dark:"After Dark · dunkel",theme_light:"Sunday · hell",theme_not_saved:"Design für diesen Tab angewendet. Browserspeicher ist nicht verfügbar; beim erneuten Öffnen kann es zurückgesetzt werden."});
const $=id=>document.getElementById(id);
$("appearance").value=window.mealfAppearance.get();
window.addEventListener("mealf:appearance",()=>{$("appearance").value=window.mealfAppearance.get();});
$("appearance").onchange=()=>{if(!window.mealfAppearance.set($("appearance").value))message("theme_not_saved");};
let locale="en", configured=false, storageStatus=null, diagnosticStatus=null, currentPage="overview";
const pageTitles={overview:"overview",household:"household_settings",security:"security",ai:"ai_settings",bring:"bring_settings",data:"data_management"};
function selectPage(key, focus=true){
  if(!Object.hasOwn(pageTitles,key))return;
  currentPage=key;
  document.querySelectorAll("[data-page]").forEach(page=>page.hidden=page.dataset.page!==key);
  document.querySelectorAll("[data-page-link]").forEach(link=>{
    if(link.dataset.pageLink===key)link.setAttribute("aria-current","page");else link.removeAttribute("aria-current");
  });
  $("page-title").dataset.i18n=pageTitles[key];
  $("page-title").textContent=words[locale][pageTitles[key]];
  if(focus){$("page-title").focus({preventScroll:true});window.scrollTo(0,0);if($("status").dataset.i18n!=="busy")message("ready");}
}
document.querySelectorAll("[data-page-link]").forEach(link=>link.onclick=event=>{event.preventDefault();selectPage(link.dataset.pageLink);});
// Read the previous device identity without replacing any session or household data.
const device=localStorage.getItem("mealf.device")||localStorage.getItem("aircooker.device")||crypto.randomUUID();
localStorage.setItem("mealf.device",device);
function translate(){
  document.documentElement.lang=locale;
  document.querySelectorAll("[data-peach]").forEach(button=>button.setAttribute("aria-label",words[locale].peach_slap));
  document.querySelectorAll("[data-i18n]").forEach(e=>e.textContent=words[locale][e.dataset.i18n]);
  for(const id of ["status","ai-key-status"]){const e=$(id);if(e.dataset.errorCode)e.textContent+=" · "+e.dataset.errorCode;}
  if($("bring-state").dataset.listId)$("bring-state").textContent+=" · "+$("bring-state").dataset.listId;
  renderStorage();renderQueueCounts();translateSessions();translateJobs();
}
function message(key){$("status").dataset.i18n=key;delete $("status").dataset.errorCode;$("status").textContent=words[locale][key]||key;}
function showError(code){const aiErrors={ai_authentication_failed:"ai_error_auth",ai_model_or_endpoint_not_found:"ai_error_model",ai_request_rejected:"ai_error_request",ai_rate_limited:"ai_error_quota",ai_test_rate_limited:"ai_error_quota",ai_timeout:"ai_error_timeout",ai_connection_failed:"ai_error_connection",ai_provider_failed:"ai_error_provider"};$("status").dataset.i18n=Object.hasOwn(aiErrors,code)?aiErrors[code]:(["http_502","http_504"].includes(code)?"gateway_error":code==="invalid_gemini_model_id"?"model_error":"error");$("status").dataset.errorCode=code;$("status").textContent=words[locale][$("status").dataset.i18n]+code;}
function renderStorage(){
  if(!storageStatus)return;
  const bytes=value=>new Intl.NumberFormat(locale,{style:"unit",unit:"megabyte",maximumFractionDigits:1}).format(value/1000000);
  $("storage").textContent=words[locale].database+": "+bytes(storageStatus.database_bytes)+" · "+words[locale].photo_storage+": "+bytes(storageStatus.media_bytes)+" · "+words[locale].free_space+": "+bytes(storageStatus.disk_free_bytes);
}
function translateSessions(){
  document.querySelectorAll(".session-row").forEach(row=>{
    const d=row.dataset;
    row.querySelector("span").textContent=(d.current==="true"?words[locale].current_session+" · ":"")+d.device+" · "+words[locale][d.revoked==="true"?"revoked":"active"]+" · "+words[locale].expires+" "+new Date(Number(d.expires)*1000).toLocaleString(locale);
  });
}
function renderQueueCounts(){
  if(!diagnosticStatus)return;
  const numbers=new Intl.NumberFormat(locale);
  $("queue-counts").textContent=["queued","running","done","failed"].map(state=>words[locale]["job_"+state]+": "+numbers.format(diagnosticStatus.job_counts[state])).join(" · ");
}
function translateJobs(){document.querySelectorAll(".job").forEach(row=>{
  const kind=({"recipe.import":"kind_import","shopping.reconcile":"kind_shopping"})[row.dataset.kind]||"kind_unknown";
  row.textContent=words[locale][kind]+" · "+(words[locale]["job_"+row.dataset.state]||words[locale].job_unknown)+(row.dataset.error?" · "+diagnosticMessage(row.dataset.error):"")+(row.dataset.created?" · "+new Date(Number(row.dataset.created)*1000).toLocaleString(locale):"");
  row.title=row.dataset.error?words[locale].diagnostic_code+row.dataset.error:"";
});}
function authenticationCopy(){
  $("page-title").dataset.i18n=configured?"login_headline":"setup_headline";
  document.querySelector(".auth-intro [data-i18n$='_joke']").dataset.i18n=configured?"login_joke":"setup_joke";
}
function signedOut(){
  $("dashboard").hidden=true; $("authentication").hidden=false;
  $("console-nav").hidden=true; $("logout").hidden=true;
  authenticationCopy();translate();
  document.body.classList.remove("authenticated");
  document.querySelectorAll('input[type="password"]').forEach(e=>e.value="");
}
function csrf(){const values=document.cookie.split("; ");return (values.find(c=>c.startsWith("mealf_csrf="))||values.find(c=>c.startsWith("aircooker_csrf=")))?.split("=")[1]||"";}
async function request(path,options={}){
  const response=await fetch(path,{...options,headers:{"Content-Type":"application/json","X-CSRF-Token":csrf(),...options.headers},credentials:"same-origin",redirect:"error"});
  if(!response.ok){
    let code="http_"+response.status;
    try{const value=(await response.json()).error?.code;if(typeof value==="string")code=value;}catch{}
    if(response.status===401){signedOut(); message("session_ended");}
    throw new Error(code);
  }
  return response.status===204?null:response.json();
}
async function action(element,work){
  const buttons=Array.from(element.querySelectorAll("button"));
  if(element.tagName==="BUTTON")buttons.push(element);
  const original=buttons.map(button=>button.disabled);
  buttons.forEach(button=>button.disabled=true); message("busy");
  try{await work();}catch(err){showError(err.message);}
  finally{buttons.forEach((button,i)=>button.disabled=original[i]);if($("status").dataset.i18n==="busy")message("ready");}
}
function put(path,body){return request(path,{method:"PUT",body:JSON.stringify(body)});}
function post(path,body={}){return request(path,{method:"POST",body:JSON.stringify(body)});}
function field(form,name){return form.elements.namedItem(name);}
Object.assign(words.en, {ai_formats:"Model input formats", ai_formats_hint:"Enable only formats supported by the selected model. Text is always enabled.", ai_images:"Images and screenshots", ai_default_hint:"Saving selects this provider and model as the default. Other provider configurations remain encrypted on the server."});
Object.assign(words.de, {ai_formats:"Eingabeformate des Modells", ai_formats_hint:"Aktiviere nur Formate, die das gewählte Modell unterstützt. Text bleibt aktiv.", ai_images:"Bilder und Screenshots", ai_default_hint:"Speichern wählt Anbieter und Modell als Standard. Andere Anbieterkonfigurationen bleiben verschlüsselt auf dem Server."});
Object.assign(words.en, {ai_model_hint:"Use the exact API model ID, for example gemini-3.8-flash, rather than its display name.",model_error:"Gemini requires an API model ID without spaces, for example gemini-3.8-flash. Code: ",gateway_error:"No readable server error details were received. Check container and reverse-proxy logs. Code: "});
Object.assign(words.de, {ai_model_hint:"Verwende die genaue API-Modell-ID, zum Beispiel gemini-3.8-flash, statt des Anzeigenamens.",model_error:"Gemini benötigt eine API-Modell-ID ohne Leerzeichen, zum Beispiel gemini-3.8-flash. Code: ",gateway_error:"Keine lesbaren Server-Fehlerdetails empfangen. Prüfe Container- und Reverse-Proxy-Logs. Code: "});
Object.assign(words.en, {ai_error_auth:"AI access was refused. Check the API key and its permissions. Code: ",ai_error_model:"AI model or endpoint not found. Check the exact API model ID and base URL. Code: ",ai_error_request:"The AI provider rejected this request. Check model options and structured output support. Code: ",ai_error_quota:"An AI request or quota limit was reached. Check limits and wait before retrying. Code: ",ai_error_timeout:"The AI provider did not reply in time. Check the configured timeout. Code: ",ai_error_connection:"The container could not connect to the AI provider. Check DNS, outbound access and certificate trust. Code: ",ai_error_provider:"The AI provider could not process the request. Check its service status. Code: "});
Object.assign(words.de, {ai_error_auth:"Der KI-Zugriff wurde abgelehnt. Prüfe API-Schlüssel und Berechtigungen. Code: ",ai_error_model:"KI-Modell oder Endpunkt nicht gefunden. Prüfe die genaue API-Modell-ID und die Basis-URL. Code: ",ai_error_request:"Der KI-Anbieter hat die Anfrage abgelehnt. Prüfe Modelloptionen und Unterstützung für strukturierte Ausgabe. Code: ",ai_error_quota:"Ein KI-Anfrage- oder Kontingentlimit wurde erreicht. Prüfe die Limits und warte vor einem neuen Versuch. Code: ",ai_error_timeout:"Der KI-Anbieter hat nicht rechtzeitig geantwortet. Prüfe das eingestellte Zeitlimit. Code: ",ai_error_connection:"Der Container konnte den KI-Anbieter nicht erreichen. Prüfe DNS, ausgehende Verbindungen und vertrauenswürdige Zertifikate. Code: ",ai_error_provider:"Der KI-Anbieter konnte die Anfrage nicht verarbeiten. Prüfe seinen Dienststatus. Code: "});
function aiFormats(profile) {
  const form=$("ai-form");
  if((profile.provider||field(form,"provider").value)==="gemini")field(form,"model").setAttribute("pattern","\\S+");else field(form,"model").removeAttribute("pattern");
  for(const format of ["image","pdf","video","youtube"]) {
    const input=field(form,"input_"+format);
    input.checked=(profile.input_formats||[]).includes(format);
    input.parentElement.hidden=!(profile.available_formats||[]).includes(format);
  }
}
function aiEnabled(){
  const form=$("ai-form"); const enabled=field(form,"enabled").checked;
  form.querySelectorAll("[data-ai-option]").forEach(input=>input.disabled=!enabled);
}
async function refreshSessions(){
  const sessions=await request("/api/v1/auth/sessions"); $("sessions").replaceChildren();
  for(const session of sessions){
    const row=document.createElement("div"); row.className="session-row";
    const label=document.createElement("span");
    label.textContent=(session.current?words[locale].current_session+" · ":"")+session.device_id.slice(0,8)+" · "+(session.revoked?words[locale].revoked:words[locale].active)+" · "+words[locale].expires+" "+new Date(session.refresh_expires*1000).toLocaleString(locale);
    row.dataset.device=session.device_id.slice(0,8);row.dataset.current=String(session.current);row.dataset.revoked=String(Boolean(session.revoked));row.dataset.expires=session.refresh_expires;
    row.append(label);
    if(!session.revoked){
      const button=document.createElement("button");button.type="button";button.className="secondary";button.textContent=words[locale].revoke;button.dataset.i18n="revoke";
      button.onclick=()=>action(button,async()=>{
        if(!confirm(words[locale].revoke_question))return;
        await request("/api/v1/auth/sessions/"+encodeURIComponent(session.id),{method:"DELETE"});
        await refreshSessions();message("saved");
      });row.append(button);
    }
    $("sessions").append(row);
  }
  translateSessions();
}
async function refresh(){
  const [diagnostics,bring,info,household,ai,status]=await Promise.all([
    request("/api/v1/admin/diagnostics"),request("/api/v1/integrations/bring/status"),
    request("/api/v1/system/info"),request("/api/v1/household"),request("/api/v1/admin/ai"),request("/api/v1/admin/status")]);
  $("identity").textContent=info.name+" · v"+info.version;
  $("authentication").hidden=true;$("dashboard").hidden=false;$("metrics").replaceChildren();
  $("console-nav").hidden=false;$("logout").hidden=false;document.body.classList.add("authenticated");selectPage(currentPage,false);
  for(const [key,value] of [["pending",status.pending_jobs],["recipes",String(status.recipes)],["bring",bring.state==="configured"?words[locale].configured:(bring.state==="not_configured"?words[locale].disabled:words[locale].verification)]]){
    const box=document.createElement("div");box.className="metric";
    const strong=document.createElement("strong");strong.textContent=value;
    if(key==="bring")strong.dataset.i18n=bring.state==="configured"?"configured":bring.state==="not_configured"?"disabled":"verification";
    const span=document.createElement("span");span.dataset.i18n=key;span.textContent=words[locale][key];box.append(strong,span);$("metrics").append(box);
  }
  storageStatus=status;renderStorage();diagnosticStatus=diagnostics;renderQueueCounts();
  const jobs=diagnostics.recent_jobs;
  $("jobs").replaceChildren();
  for(const job of jobs){const row=document.createElement("div");row.className="job";row.dataset.kind=job.kind;row.dataset.state=job.state;row.dataset.error=job.error_code||"";row.textContent=job.kind+" · "+job.state+(job.error_code?" · "+job.error_code:"");$("jobs").append(row);}
  if(!jobs.length){$("jobs").dataset.i18n="empty";$("jobs").textContent=words[locale].empty;}else{delete $("jobs").dataset.i18n;}
  $("recent-imports").replaceChildren();
  delete $("recent-imports").dataset.i18n;
  for(const item of diagnostics.recent_imports){const row=document.createElement("div");row.className="job";row.dataset.kind="recipe.import";row.dataset.state=item.state;row.dataset.error=item.error_code||"";row.dataset.created=item.created_at;$("recent-imports").append(row);}
  if(!diagnostics.recent_imports.length){$("recent-imports").dataset.i18n="empty_imports";$("recent-imports").textContent=words[locale].empty_imports;}
  translateJobs();
  const h=$("household-form");for(const key of ["name","timezone","language"])field(h,key).value=household[key];
  const form=$("ai-form");field(form,"enabled").checked=ai.enabled;aiFormats(ai);
  for(const key of ["provider","base_url","model","timeout","max_content","requests_per_hour"]){
    if(ai[key]!==null&&ai[key]!==undefined)field(form,key).value=ai[key];
  }
  for(const key of ["structured_output","allow_local_http"])field(form,key).checked=ai[key];
  $("ai-key-status").dataset.i18n=ai.key_configured?"key_saved":"no_key";$("ai-key-status").dataset.errorCode=ai.configuration_error||"";
  $("ai-key-status").textContent=words[locale][ai.key_configured?"key_saved":"no_key"]+(ai.configuration_error?" · "+ai.configuration_error:"");
  $("bring-retry").disabled=!bring.list_id;
  $("bring-state").dataset.i18n=bring.state;$("bring-state").dataset.listId=bring.list_id||"";
  $("bring-state").textContent=(words[locale][bring.state]||bring.state)+(bring.list_id?" · "+bring.list_id:"");
  aiEnabled();await refreshSessions();message("ready");
}
$("language").onchange=()=>{locale=$("language").value;translate();};
$("login").onsubmit=event=>{event.preventDefault();const form=event.target;
  action(form,async()=>{
    const data=Object.fromEntries(new FormData(form));const auth={username:data.username,password:data.password,device_id:device};
    try{
      if(!configured){
        // Account creation carries the administrator token only in its header.
        const session=await request("/api/v1/setup",{method:"POST",headers:{"X-Setup-Token":data.token},body:JSON.stringify({...auth,name:data.name,timezone:data.timezone,language:locale})});
        configured=true;$("setup-fields").hidden=true;
        await request("/api/v1/auth/logout",{method:"POST",headers:{Authorization:"Bearer "+session.access_token},body:"{}"});
      }
      await post("/api/v1/admin/login",auth);form.reset();await refresh();
    }finally{field(form,"password").value="";field(form,"token").value="";}
  });
};
$("household-form").onsubmit=event=>{event.preventDefault();action(event.target,async()=>{
  await put("/api/v1/household",Object.fromEntries(new FormData(event.target)));message("saved");
});};
$("password-form").onsubmit=event=>{event.preventDefault();action(event.target,async()=>{
  try{await post("/api/v1/auth/password",Object.fromEntries(new FormData(event.target)));signedOut();message("session_ended");}
  finally{event.target.reset();}
});};
field($("ai-form"),"enabled").onchange=aiEnabled;
field($("ai-form"),"provider").onchange=async()=>{
  const form=$("ai-form"), selected=field(form,"provider").value;
  if(form.dataset.profileLoading)return;
  form.dataset.profileLoading="true";form.setAttribute("aria-busy","true");
  form.querySelectorAll("input,select").forEach(input=>input.disabled=true);
  try{await action(form,async()=>{
  field(form,"api_key").value="";field(form,"clear_key").checked=false;
  const catalog=await request("/api/v1/admin/ai/providers");
  const profile=catalog.profiles.find(p=>p.provider===selected);
  if(!profile)return;
  for(const name of ["base_url","model","timeout","max_content","requests_per_hour"])field(form,name).value=profile[name]??"";
  for(const name of ["structured_output","allow_local_http"])field(form,name).checked=profile[name];
  aiFormats(profile);$("ai-key-status").dataset.i18n=profile.key_configured?"key_saved":"no_key";
  $("ai-key-status").textContent=words[locale][profile.key_configured?"key_saved":"no_key"];
  });}finally{
    delete form.dataset.profileLoading;form.removeAttribute("aria-busy");
    field(form,"enabled").disabled=false;aiEnabled();
  }
};
$("ai-form").onsubmit=event=>{event.preventDefault();const form=event.target;
  if(form.dataset.profileLoading)return;
  action(form,async()=>{
    const data={enabled:field(form,"enabled").checked};
    if(data.enabled){
      for(const key of ["provider","base_url","model"])data[key]=field(form,key).value;
      for(const key of ["timeout","max_content","requests_per_hour"])data[key]=Number(field(form,key).value);
      for(const key of ["structured_output","allow_local_http"])data[key]=field(form,key).checked;
      data.input_formats=["text", ...["image","pdf","video","youtube"].filter(format=>!field(form,"input_"+format).parentElement.hidden&&field(form,"input_"+format).checked)];
      const key=field(form,"api_key").value.trim();if(key)data.api_key=key;
      if(field(form,"clear_key").checked)data.api_key="";
    }
    try{await put("/api/v1/admin/ai",data);await refresh();message("saved");}
    finally{field(form,"api_key").value="";field(form,"clear_key").checked=false;}
  });
};
$("ai-test").onclick=()=>action($("ai-test"),async()=>{await post("/api/v1/admin/ai/test");message("ai_validated");});
$("bring-form").onsubmit=event=>{event.preventDefault();const form=event.target;
  action(form,async()=>{try{await post("/api/v1/integrations/bring/connect",Object.fromEntries(new FormData(form)));message("bring_saved");}
  finally{field(form,"password").value="";}});
};
$("bring-test").onclick=()=>action($("bring-test"),async()=>{
  const result=await request("/api/v1/integrations/bring/lists");$("bring-list").replaceChildren();
  for(const list of result.lists){const option=document.createElement("option");option.value=list.id;option.textContent=list.name;$("bring-list").append(option);}
  $("bring-select").disabled=!result.lists.length;message("ready");
});
$("bring-select").onclick=()=>action($("bring-select"),async()=>{
  await put("/api/v1/integrations/bring/configuration",{list_id:$("bring-list").value});await refresh();message("bring_selected");
});
$("bring-retry").onclick=()=>action($("bring-retry"),async()=>{await post("/api/v1/integrations/bring/reconcile");message("queued");});
$("bring-disconnect").onclick=()=>action($("bring-disconnect"),async()=>{
  if(!confirm(words[locale].disconnect_question))return;
  await request("/api/v1/integrations/bring/disconnect",{method:"DELETE"});$("bring-list").replaceChildren();$("bring-select").disabled=true;await refresh();message("saved");
});
$("import-form").onsubmit=event=>{event.preventDefault();action(event.target,async()=>{
  const file=$("import-file").files[0];if(!file)return;
  if(!confirm(words[locale].import_question))return;
  if(file.size>280*1024*1024)throw new Error("archive_size_limit");
  if(file.name.toLowerCase().endsWith(".zip"))await request("/api/v1/admin/import/archive",{method:"POST",body:file,headers:{"Content-Type":"application/zip"}});
  else{
    if(file.size>8*1024*1024)throw new Error("json_size_limit");
    await post("/api/v1/admin/import",JSON.parse(await file.text()));
  }
  event.target.reset();await refresh();message("imported");
});};
$("logout").onclick=()=>action($("logout"),async()=>{await post("/api/v1/admin/logout");signedOut();message("session_ended");});
$("reload").onclick=()=>action($("reload"),refresh);
$("export").onclick=()=>{window.location.assign("/api/v1/admin/export/archive");};
(async()=>{try{
  const info=await request("/api/v1/system/info");configured=info.configured;$("setup-fields").hidden=configured;authenticationCopy();
  $("identity").textContent=info.name+" · v"+info.version;translate();if(configured)await refresh();
}catch(err){showError(err.message);}})();
