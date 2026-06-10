export default function VideoCanvasHidden({ videoRef, canvasRef }) {
    return (
        <>
            <video ref={videoRef} autoPlay playsInline muted style={{ display: 'none' }}></video>
            <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
        </>
    );
}
