import { useEffect, useRef, useState } from "react"
import { Link } from "react-router-dom"
import { Room, RoomEvent } from "livekit-client"
import { api } from "../api/client"

function describeError(err) {
  if (!err) return "Unknown error"
  if (typeof err === "string") return err
  if (err.message) return err.message
  try {
    return JSON.stringify(err, Object.getOwnPropertyNames(err))
  } catch {
    return String(err)
  }
}

export default function TestCall() {
  const [status, setStatus] = useState("idle") // idle | connecting | active | ended
  const [lines, setLines] = useState([])
  const [live, setLive] = useState(null)
  const [error, setError] = useState("")
  const [micSpeaking, setMicSpeaking] = useState(false)
  const [eventLog, setEventLog] = useState([])
  const [micTestLevel, setMicTestLevel] = useState(0)
  const [micTestActive, setMicTestActive] = useState(false)
  const [micTestError, setMicTestError] = useState("")
  const [testLeadId, setTestLeadId] = useState(null)
  const roomRef = useRef(null)
  const micTestStreamRef = useRef(null)
  const micTestAudioCtxRef = useRef(null)
  const micTestRafRef = useRef(null)

  const logEvent = (text) => {
    const stamp = new Date().toLocaleTimeString()
    setEventLog((prev) => [...prev.slice(-49), `${stamp}  ${text}`])
  }

  const stopMicTest = async () => {
    if (micTestRafRef.current) cancelAnimationFrame(micTestRafRef.current)
    micTestStreamRef.current?.getTracks().forEach((t) => t.stop())
    if (micTestAudioCtxRef.current) {
      try {
        await micTestAudioCtxRef.current.close()
      } catch {
        // already closed
      }
    }
    micTestStreamRef.current = null
    micTestAudioCtxRef.current = null
    micTestRafRef.current = null
    setMicTestActive(false)
    setMicTestLevel(0)
  }

  // Bypasses LiveKit entirely: raw getUserMedia + an AnalyserNode volume meter.
  // If this bar never moves, the problem is the browser/OS/hardware mic path,
  // not anything in the LiveKit/agent config — narrows down where to look next.
  const startMicTest = async () => {
    setMicTestError("")
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      micTestStreamRef.current = stream
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      const audioCtx = new AudioCtx()
      micTestAudioCtxRef.current = audioCtx
      const source = audioCtx.createMediaStreamSource(stream)
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 512
      source.connect(analyser)
      const data = new Uint8Array(analyser.frequencyBinCount)
      setMicTestActive(true)
      const tick = () => {
        analyser.getByteTimeDomainData(data)
        let sumSquares = 0
        for (let i = 0; i < data.length; i++) {
          const v = (data[i] - 128) / 128
          sumSquares += v * v
        }
        const rms = Math.sqrt(sumSquares / data.length)
        setMicTestLevel(Math.min(1, rms * 4))
        micTestRafRef.current = requestAnimationFrame(tick)
      }
      tick()
    } catch (err) {
      setMicTestError(describeError(err) || "Could not access microphone")
    }
  }

  useEffect(() => {
    return () => {
      roomRef.current?.disconnect()
      stopMicTest()
    }
  }, [])

  const start = async () => {
    if (status === "connecting" || status === "active") return
    setStatus("connecting")
    if (roomRef.current) {
      await roomRef.current.disconnect()
      roomRef.current = null
    }
    await stopMicTest()
    setError("")
    setLines([])
    setLive(null)
    setMicSpeaking(false)
    setEventLog([])
    setTestLeadId(null)
    try {
      const { livekit_url, token, test_lead_id } = await api("/api/assistant/preview")
      if (!livekit_url || !token) {
        setError("LiveKit is not configured in the backend .env")
        setStatus("idle")
        return
      }
      setTestLeadId(test_lead_id)
      const room = new Room()
      roomRef.current = room

      room.on(RoomEvent.Disconnected, () => {
        setStatus("ended")
        setLive(null)
        setMicSpeaking(false)
        logEvent("disconnected")
        roomRef.current = null
      })
      room.on(RoomEvent.TrackSubscribed, (track) => {
        if (track.kind === "audio") {
          track.attach() // agent's voice — attaches its own hidden <audio> element
        }
      })
      room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
        setMicSpeaking(speakers.some((p) => p.identity === room.localParticipant.identity))
      })

      // The agent worker streams its own live transcript over LiveKit's text-stream
      // API (registered on the 'lk.transcription' topic) — this replaces Vapi's
      // "message"/"transcript" events from the old integration.
      room.registerTextStreamHandler("lk.transcription", async (reader, participantInfo) => {
        const role = participantInfo.identity === room.localParticipant.identity ? "user" : "assistant"
        const isFinal = reader.info.attributes?.["lk.transcription_final"] === "true"
        let text = ""
        for await (const chunk of reader) {
          text += chunk
          setLive({ role, text })
        }
        logEvent(`transcript ${isFinal ? "final" : "partial"} [${role}]: ${text}`)
        if (!isFinal || !text) return
        setLive(null)
        setLines((prev) => {
          const last = prev[prev.length - 1]
          if (last && last.role === role) {
            const merged = [...prev]
            merged[merged.length - 1] = { role, text: `${last.text} ${text}`.trim() }
            return merged
          }
          return [...prev, { role, text }]
        })
      })

      await room.connect(livekit_url, token)
      await room.localParticipant.setMicrophoneEnabled(true)
      setStatus("active")
      logEvent("connected")
    } catch (err) {
      setError(describeError(err))
      setStatus("idle")
    }
  }

  const stop = async () => {
    setStatus("ended")
    await roomRef.current?.disconnect()
    roomRef.current = null
  }

  return (
    <div>
      <div className="page-head">
        <h1>Test call</h1>
      </div>
      <div className="card narrow">
        <h2>Step 1: test your microphone{micTestActive ? " — listening" : ""}</h2>
        <p className="muted" style={{ marginBottom: 8 }}>
          Checks your browser/OS mic access directly, with no LiveKit call involved.
          Do this first if your voice wasn't picked up in a call.
        </p>
        <div className="progress-bar" style={{ marginBottom: 12 }}>
          <div
            className="progress-fill"
            style={{ width: `${Math.round(micTestLevel * 100)}%`, transition: "width 80ms linear" }}
          />
        </div>
        <div className="actions">
          {!micTestActive
            ? <button className="btn" onClick={startMicTest}>Test microphone</button>
            : <button className="btn" onClick={stopMicTest}>Stop mic test</button>}
        </div>
        {micTestError && <div className="error">{micTestError}</div>}
      </div>
      <div className="card narrow" style={{ marginTop: 20 }}>
        <h2>Step 2: talk to the assistant in your browser</h2>
        <p className="muted">
          Dispatches the same LiveKit agent (app/livekit_agent.py) real phone calls use, no
          phone number needed. Allow microphone access when prompted.
        </p>
        {testLeadId && (
          <p className="muted" style={{ marginTop: 8 }}>
            This test call is linked to a reusable test lead named "Nasir Sultan" — once the call
            ends, check <Link to={`/leads/${testLeadId}`}>its lead detail page</Link> to
            verify the extracted data actually saved to the database.
          </p>
        )}
        <div className="actions" style={{ marginTop: 14 }}>
          {status !== "active" && status !== "connecting" && (
            <button className="btn primary" onClick={start}>Start test call</button>
          )}
          {(status === "active" || status === "connecting") && (
            <button className="btn danger" onClick={stop}>End call</button>
          )}
        </div>
        {status === "connecting" && <p className="muted" style={{ marginTop: 12 }}>Connecting...</p>}
        {status === "active" && <div className="notice" style={{ marginTop: 12 }}>Call in progress, speak into your microphone.</div>}
        {status === "ended" && <p className="muted" style={{ marginTop: 12 }}>Call ended.</p>}
        {error && <div className="error">{error}</div>}
      </div>
      {(status === "active" || status === "connecting") && (
        <div className="card narrow" style={{ marginTop: 20 }}>
          <h2>Your mic reaching LiveKit</h2>
          <p className="muted" style={{ marginBottom: 8 }}>
            Lights up only while LiveKit detects you speaking. If it never lights up while you
            talk, it's a mic/permission issue. If it lights up but no transcript ever
            appears below, your audio is arriving but not being transcribed.
          </p>
          <div className={`pill ${micSpeaking ? "pill-live" : "pill-off"}`}>
            {micSpeaking ? "Voice detected" : "Silent"}
          </div>
        </div>
      )}
      <div className="card narrow" style={{ marginTop: 20 }}>
        <h2>Live transcript</h2>
        {lines.length === 0 && !live && <p className="muted">No transcript yet.</p>}
        {lines.map((line, i) => (
          <div className={`transcript-line role-${line.role}`} key={i}>
            <span className="role">{line.role === "assistant" ? "Assistant" : "You"}:</span> {line.text}
          </div>
        ))}
        {live && (
          <div className={`transcript-line role-${live.role} live`}>
            <span className="role">{live.role === "assistant" ? "Assistant" : "You"}:</span> {live.text}
          </div>
        )}
      </div>
      <div className="card narrow" style={{ marginTop: 20 }}>
        <h2>Raw event log</h2>
        {eventLog.length === 0 && <p className="muted">No events yet.</p>}
        <pre className="transcript">{eventLog.join("\n")}</pre>
      </div>
    </div>
  )
}
