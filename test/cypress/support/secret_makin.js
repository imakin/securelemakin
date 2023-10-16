function generateFingerprint() {
    let timeZone = new Date().getTimezoneOffset();
    let navkeys = Object.keys(navigator.__proto__);
    navkeys.sort();
    let keys_used = [];
    var ids = "";
    navkeys.forEach((k)=>{
        let v = navigator[k]
        if (typeof(v)=='string' && v.length>0){
            keys_used.push(k);
            ids += v + ' ';
        }
    })
    console.log(`using ${keys_used}`)
    let str = ids
    let hash = 0;
    for (let i = 0, len = str.length; i < len; i++) {
        let chr = str.charCodeAt(i);
        hash = (hash << 5) - hash + chr;
        // hash |= 0; // Convert to 32bit integer
    }
    return hash;
}
function vulnerable_encrypt(msg){
    var fp = generateFingerprint();
    var result = "";
    for (let i=0, len = msg.length; i<len;i++ ){
        let ord = msg.charCodeAt(i);
        if (result.length>0) result += ' ';
        result += ""+(
            fp+ord
        );
    }
    return result;
}
function vulnerable_decrypt(chiper){
    var fp = generateFingerprint();
    var result = [];
    let split = chiper.split(' ');
    for (let i=0,len = split.length;i<len;i++){
        let v = parseInt(split[i]) - fp;
        result.push(v);
    }
    console.log(result)
    return String.fromCharCode(...result);
}
vulnerable_decrypt(vulnerable_encrypt('example'));

Cypress.Commands.add('get_secret_key', () => {
    return 'password contoh';
});

Cypress.Commands.add('fingerprint',()=>{
    let fp = generateFingerprint();
    console.log(fp);
    Cypress.cy.get('body').then((body)=>{
        console.log(body);
        let div = document.createElement('div');
        div.innerHTML = fp;
        body[0].appendChild(div);
    })
})

Cypress.Commands.add('vulnerable_encrypt_type',(msg,element_selector)=>{
    const secret = vulnerable_encrypt(msg);
    Cypress.cy.get(element_selector).type(secret);
})
Cypress.Commands.add('vulnerable_decrypt_type',(chiper,element_selector)=>{
    const secret = vulnerable_decrypt(chiper);
    Cypress.cy.get(element_selector).type(secret);
})