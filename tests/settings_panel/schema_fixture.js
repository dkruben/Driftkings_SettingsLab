const path=require('path'), {execFileSync}=require('child_process');
module.exports=JSON.parse(execFileSync(process.env.PYTHON||'python',[path.join(__dirname,'export_schema.py')],
    {encoding:'utf8',maxBuffer:16*1024*1024}));
