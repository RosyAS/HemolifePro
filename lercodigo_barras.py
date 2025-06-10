import cv2
from pyzbar.pyzbar import decode

def ler_codigo():
    cap = cv2.VideoCapture(0)
    while True:
        _, frame = cap.read()
        for barcode in decode(frame):
            dados = barcode.data.decode("utf-8")
            print(f"📦 Código Lido: {dados}")
            cap.release()
            cv2.destroyAllWindows()
            return dados
        cv2.imshow("Leitor de Código", frame)
        if cv2.waitKey(1) == 27:
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    ler_codigo()
