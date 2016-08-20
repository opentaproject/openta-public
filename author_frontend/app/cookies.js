//This is googles cookie reading function
function getcookie(a){
    var d=[],
        e=document.cookie.split(";");
    a=RegExp("^\\s*"+a+"=\\s*(.*?)\\s*$");
    for(var b=0;b<e.length;b++){
        var f=e[b].match(a);
        f&&d.push(f[1])
    }
    return d
}

export {getcookie}
