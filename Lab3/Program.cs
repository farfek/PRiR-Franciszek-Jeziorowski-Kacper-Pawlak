using System;
using System.IO;
using System.Net.Sockets;

class Program
{
    static byte[] ReceiveAll(BinaryReader reader)
    {
        int length = reader.ReadInt32();
        byte[] data = reader.ReadBytes(length);
        if (data.Length != length)
            throw new IOException("Połączenie zerwane");
        return data;
    }

    static void SendAll(BinaryWriter writer, byte[] data)
    {
        writer.Write(data.Length);
        writer.Write(data);
        writer.Flush();
    }

    static double[,] Sobel(byte[,] fragment, int yStart, int yEnd)
    {
        int h = fragment.GetLength(0);
        int w = fragment.GetLength(1);
        double[,] wynik = new double[yEnd - yStart, w];

        int[,] gx = { { -1, 0, 1 }, { -2, 0, 2 }, { -1, 0, 1 } };
        int[,] gy = { { -1, -2, -1 }, { 0, 0, 0 }, { 1, 2, 1 } };

        for (int y = yStart; y < yEnd; y++)
        {
            for (int x = 0; x < w; x++)
            {
                double sx = 0;
                double sy = 0;
                for (int dy = -1; dy <= 1; dy++)
                {
                    for (int dx = -1; dx <= 1; dx++)
                    {
                        int yy = Math.Min(Math.Max(y + dy, 0), h - 1);
                        int xx = Math.Min(Math.Max(x + dx, 0), w - 1);
                        int pixel = fragment[yy, xx];
                        sx += pixel * gx[dy + 1, dx + 1];
                        sy += pixel * gy[dy + 1, dx + 1];
                    }
                }
                wynik[y - yStart, x] = Math.Sqrt(sx * sx + sy * sy);
            }
        }
        return wynik;
    }

    static void Main()
    {
        using TcpClient client = new TcpClient("10.183.5.182", 2040);
        using NetworkStream stream = client.GetStream();
        using BinaryReader reader = new BinaryReader(stream);
        using BinaryWriter writer = new BinaryWriter(stream);

        byte[] message = ReceiveAll(reader);
        using MemoryStream input = new MemoryStream(message);
        using BinaryReader data = new BinaryReader(input);
        int h = data.ReadInt32();
        int w = data.ReadInt32();
        int yStart = data.ReadInt32();
        int yEnd = data.ReadInt32();

        byte[,] fragment = new byte[h, w];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
                fragment[y, x] = data.ReadByte();

        double[,] wynik = Sobel(fragment, yStart, yEnd);

        using MemoryStream output = new MemoryStream();
        using (BinaryWriter result = new BinaryWriter(output, System.Text.Encoding.UTF8, true))
        {
            result.Write(yEnd - yStart);
            result.Write(w);
            for (int y = 0; y < yEnd - yStart; y++)
                for (int x = 0; x < w; x++)
                    result.Write(wynik[y, x]);
        }

        SendAll(writer, output.ToArray());
        Console.WriteLine("Fragment przetworzony i wysłany z powrotem do serwera");
    }
}
