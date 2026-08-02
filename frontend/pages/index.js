import React, {useState} from 'react'

export default function Home() {
  const [file, setFile] = useState(null)
  const [url, setUrl] = useState('')
  const [status, setStatus] = useState('')
  const [result, setResult] = useState(null)

  const backend = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus('Uploading...')
    const form = new FormData()
    if (file) form.append('file', file)
    if (url) form.append('url', url)

    try {
      const res = await fetch(`${backend}/upload`, {
        method: 'POST',
        body: form
      })
      const data = await res.json()
      if (res.ok) {
        setResult(data)
        setStatus('Done')
      } else {
        setStatus('Error: ' + (data.detail || JSON.stringify(data)))
      }
    } catch (err) {
      setStatus('Error: ' + String(err))
    }
  }

  return (
    <div style={{maxWidth:700, margin:'40px auto', fontFamily:'Arial, sans-serif'}}>
      <h1>Clip.web — MVP</h1>
      <p>Upload a VOD or paste a public Twitch/YouTube VOD URL. The server will return a short highlight clip (20s) for testing.</p>

      <form onSubmit={handleSubmit}>
        <div style={{marginBottom:12}}>
          <label>Upload file: </label>
          <input type="file" onChange={(e)=>setFile(e.target.files[0])} />
        </div>
        <div style={{marginBottom:12}}>
          <label>Or paste video URL: </label>
          <input style={{width:'100%'}} value={url} onChange={(e)=>setUrl(e.target.value)} placeholder="https://..." />
        </div>
        <button type="submit">Generate Clip</button>
      </form>

      <div style={{marginTop:20}}>
        <strong>Status:</strong> {status}
      </div>

      {result && (
        <div style={{marginTop:20}}>
          <h3>Result</h3>
          <p>Clip URL: <a href={result.clip_url} target="_blank" rel="noreferrer">{result.clip_url}</a></p>
          {result.srt_url && <p>SRT: <a href={result.srt_url} target="_blank" rel="noreferrer">{result.srt_url}</a></p>}
        </div>
      )}
    </div>
  )
}
