// React specific import

function applyshortcuts(input) {
  var shortcuts = {
    // '/(\([^\)]+\))\.(\([^\)]+\))/':'dot(\$1,\$2)',
    //'\(a\).\(b\)': 'dot\(\$1,\$2\)',
    Ö: '[',
    Ä: ']',
    Å: '^',
    ä: ')',
    ö: '(',
    å: '|'
    // 'aa': 'A', 'bb': 'B', 'cc': 'C', 'dd': 'D',
    // 'ee': 'E', 'ff': 'F', 'gg': 'G', 'hh': 'H', 'ii': 'I', 'jj': 'J',
    //'kk': 'K', 'll': 'L', 'mm': 'M', 'nn': 'N', 'oo': 'O', 'pp': 'P',
    // 'qq': 'Q', 'rr': 'R', 'ss': 'S', 'tt': 'T', 'uu': 'U','vv': 'V',
    // 'ww': 'W', 'xx': 'X', 'yy': 'Y', 'zz': 'Z', 'p  ': '+',
    // 'm  ': '-', 'd  ': '/', 'x  ': '*'
  };

  for (var key in shortcuts) {
    input = input.replace(key, shortcuts[key]);
  }
  var dots = [
    /\(([^(|]+\([^(|]+)\)\s*\.\(([^(]+\([^(]+)\)/,
    /\(([^(|]+\([^(|]+)\)\s*\.(\w+)\s/,
    /\(([^)|]+)\)\.\(([^)|]+)\)/,
    /(\w+)\.\(([^)|]+)\)/,
    /\(([^)|]+)\)\.(\w+)\s/,
    /([A-Za-z]+\w*)\.(\w+\s*)\s/,
    /([A-Za-z]+\w*)\.(\([^)|]+\)\s*)/
  ];

  var cross = [
    /\(([^(|]+\([^(|]+)\)\s*@(\w+)\s/,
    /\(([^)|]+)\)\s*@\s*\(([^)|]+)\)/,
    /(\w+)\s*@\s*\(([^)|]+)\)/,
    /\(([^)|]+)\)\s*@\s*(\w+\s)/,
    /([A-Za-z]+\w*)\s*@\s*(\w+[\s)])/
  ];

  /* var cross =  [ 
                /\(([^(|]+\([^(|]+)\)\s*@\(([^(]+\([^(]+)\)/,
                /\(([^(|]+\([^(|]+)\)\s*@(\w+)\s/,
                /\(([^)|]+)\)@\(([^)|]+)\)/,
                 /(\w+)@\(([^)|]+)\)/,
                 /\(([^)|]+)\)@(\w+)\s/,
                 /([A-Za-z]+\w*)@(\w+\s*)\s/,
                 /([A-Za-z]+\w*)@(\([^)|]+\)\s*)/
                 ]

*/

  for (var i = 0; i < cross.length; i++) {
    input = input.replace(cross[i], 'cross($1,$2)');
  }
  var it = 0;
  while (true) {
    var prev = input;
    for (var i = 0; i < dots.length; i++) {
      input = input.replace(dots[i], '  dot( $1 , $2 ) ');
    }
    if (prev == input) {
      break;
    }
    console.log('INPUT = ', input);
    it = it + 1;
  }

  return input;
}

export { applyshortcuts };
