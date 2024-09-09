function modexp(base_str, exp_str, modulus_str) {
    //effectively operate base**exp%mod
    //but might be open to timed attack
    let result  = new BN('1',10);
    let base    = BN.isBN(base_str)?    base_str    : new BN(base_str,10);
    let exp     = BN.isBN(exp_str) ?    exp_str     : new BN(exp_str,10);
    let modulus = BN.isBN(modulus_str)? modulus_str : new BN(modulus_str,10);
    let zero = new BN(0,10);
    let two = new BN(2,10);
    while (exp.gt(zero)) {
        if (exp.isOdd()) {
            //~ result = (result * base) % modulus;
            result = result.mul(base)
            result = result.mod(modulus)
        }
        //~ base = (base * base) % modulus;
        base = base.mul(base);
        base = base.mod(modulus);
        //~ exp = exp / 2n;
        exp = exp.div(two)
    }
    return result;
}
function asyml_enc(message, pub, n, strongpad=false){
    let ppad = n=>{
        if (strongpad) return pad(n)
        else return n;
    }
    chiper = new Array(message.length);
    for (var i=0;i<message.length;i++){
        chiper[i] = modexp(ppad(message.charCodeAt(i)), pub, n).toString(10);
    }
    return chiper;
}

function asyml_dec(chiper, sec, n, strongpad=false){
    let uunpad = n=>{
        if (strongpad) return unpad(n);
        else return n;
    }
    msg = new Array(chiper.length);
    for (var i=0;i<chiper.length;i++){
        let d = modexp(
            new BN(chiper[i],10),
            sec,
            n
        );
        d = uunpad(BigInt(d.toString()));
        msg[i] = String.fromCharCode(Number(d));
    }
    return msg.join('');
}

function pad(charcode){
    //dont confuse BigInt with BN()
    let r = BigInt(charcode);
    let arr = new Uint8Array(2);
    window.crypto.getRandomValues(arr);
    let arr1 = BigInt(arr[0]);
    let arr2 = BigInt(arr[1]);
    arr2 = arr2<<24n;
    r = r<<8n;
    r = r | arr1;
    r = r | arr2;
    return r;
}

function unpad(padded){
    return (
        padded & 0x00ffff00n
    )>>8n;
}


window.test = function(strongpad=true){
    msg = 'Bismillah! Makin'
    console.log(msg);
    
    //~ n =   new BN('288230305553188811',10);
    //~ pub = new BN('166539391122083293',10);
    //~ sec = new BN('239407394176360885',10);
    //4205330879736829743275749667, 2763057631687086340728083891, 1686916015223413142340260699,
    n =   new BN('4205330879736829743275749667',10);
    pub = new BN('2763057631687086340728083891',10);
    sec = new BN('1686916015223413142340260699',10);
    chiper = asyml_enc(msg, pub, n, strongpad);
    console.log(chiper);
    decoded = asyml_dec(chiper, sec, n, strongpad);
    console.log("decoded:",decoded)
}

window.testpad = ()=>{
    let v = 2500;
    let pv = pad(v);
    let uv = unpad(pv);
    console.log(pv);
    console.log(uv);
}