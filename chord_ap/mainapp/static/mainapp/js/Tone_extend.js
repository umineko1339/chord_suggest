function test_sound(){
    
// 音源の「Tone.Synth()」を作り、マスター出力に接続
var synth = new Tone.Synth().toMaster();

// 中央の「ド(C4)」を4分音符で発音する
synth.triggerAttackRelease( 'C4', '4n' );
    
}

function test_js(){
    
alert('JavaScriptのアラート');
    
}