const photoInput=document.getElementById('photoInput');
const dropzone=document.getElementById('dropzone');
const previewWrap=document.getElementById('previewWrap');
const preview=document.getElementById('preview');
const generateBtn=document.getElementById('generateBtn');
const emptyState=document.getElementById('emptyState');
const loadingState=document.getElementById('loadingState');
const resultImage=document.getElementById('resultImage');
const resultActions=document.getElementById('resultActions');
const resultStatus=document.getElementById('resultStatus');
const toast=document.getElementById('toast');
let selectedFile=null;
let resultUrl=null;

function notify(message){toast.textContent=message;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),3200)}
function setFile(file){
  if(!file)return;
  if(!['image/jpeg','image/png','image/webp'].includes(file.type)){notify('JPG, PNG yoki WEBP formatini tanlang.');return}
  if(file.size>10*1024*1024){notify('Rasm hajmi 10 MB dan oshmasin.');return}
  selectedFile=file;
  preview.src=URL.createObjectURL(file);
  dropzone.classList.add('hidden');
  previewWrap.classList.remove('hidden');
  generateBtn.disabled=false;
  clearResult();
}
function clearResult(){
  if(resultUrl){URL.revokeObjectURL(resultUrl);resultUrl=null}
  resultImage.classList.add('hidden');resultActions.classList.add('hidden');
  emptyState.classList.remove('hidden');loadingState.classList.add('hidden');
  resultStatus.textContent='KUTILMOQDA';
}
function removeFile(){
  selectedFile=null;photoInput.value='';preview.src='';
  previewWrap.classList.add('hidden');dropzone.classList.remove('hidden');
  generateBtn.disabled=true;clearResult();
}
photoInput.addEventListener('change',e=>setFile(e.target.files[0]));
document.getElementById('removePhoto').addEventListener('click',removeFile);
document.querySelectorAll('.style-option input').forEach(input=>input.addEventListener('change',()=>{
  document.querySelectorAll('.style-option').forEach(el=>el.classList.toggle('selected',el.querySelector('input').checked));
}));
['dragenter','dragover'].forEach(name=>dropzone.addEventListener(name,e=>{e.preventDefault();dropzone.classList.add('dragover')}));
['dragleave','drop'].forEach(name=>dropzone.addEventListener(name,e=>{e.preventDefault();dropzone.classList.remove('dragover')}));
dropzone.addEventListener('drop',e=>setFile(e.dataTransfer.files[0]));

async function generate(){
  if(!selectedFile)return;
  generateBtn.disabled=true;emptyState.classList.add('hidden');resultImage.classList.add('hidden');resultActions.classList.add('hidden');
  loadingState.classList.remove('hidden');resultStatus.textContent='YARATILMOQDA';
  const form=new FormData();form.append('image',selectedFile);form.append('style',document.querySelector('input[name="style"]:checked').value);
  try{
    const response=await fetch('/api/generate',{method:'POST',body:form});
    const data=await response.json();
    if(!response.ok)throw new Error(data.detail||'Xatolik yuz berdi.');
    const bytes=Uint8Array.from(atob(data.image),c=>c.charCodeAt(0));
    const blob=new Blob([bytes],{type:data.mime_type||'image/jpeg'});
    if(resultUrl)URL.revokeObjectURL(resultUrl);
    resultUrl=URL.createObjectURL(blob);
    resultImage.src=resultUrl;resultImage.classList.remove('hidden');
    loadingState.classList.add('hidden');resultActions.classList.remove('hidden');
    resultStatus.textContent='TAYYOR';notify('Portret tayyor! Yuzni asl surat bilan solishtirib ko‘ring.');
  }catch(error){
    loadingState.classList.add('hidden');emptyState.classList.remove('hidden');
    resultStatus.textContent='XATOLIK';notify(error.message);
  }finally{generateBtn.disabled=!selectedFile}
}
generateBtn.addEventListener('click',generate);
document.getElementById('retryBtn').addEventListener('click',generate);
document.getElementById('downloadBtn').addEventListener('click',()=>{
  if(!resultUrl)return;
  const link=document.createElement('a');link.href=resultUrl;link.download='uniform-ai-portrait-3x4.jpg';document.body.appendChild(link);link.click();link.remove();
});
