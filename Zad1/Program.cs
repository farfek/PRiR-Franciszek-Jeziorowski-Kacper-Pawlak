using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;

namespace Semaphore
{
    class Program
    {
        static int coalDeposit;
        static int warehouse;

        static int vehicleCapacity = 200;

        static SemaphoreSlim mineSemaphore;
        static SemaphoreSlim warehouseSemaphore;
        static int line = 0;
        static object lockObject = new object();

        static void Main(string[] args)
        {
            double timeForOneMiner = 0;

            for (int miners = 1; miners <= 6; miners++)
            {
                Console.WriteLine($"Symulacja dla {miners} górników");
                double time = RunSimulation(miners);

                if (miners == 1)
                {
                    timeForOneMiner = time;
                }

                double speedup = timeForOneMiner / time;
                double efficiency = speedup / miners;
                Console.SetCursorPosition(0, line);
                Console.WriteLine(

                    $"Liczba górników: {miners}, " +
                    $"czas: {time:F2} s, " +
                    $"przyśpieszenie: {speedup:F2}, " +
                    $"efektywność: {efficiency:F2}"
                );
                line += 1;
            }
        }

        static double RunSimulation(int minersCount)
        {
            coalDeposit = 2000;
            warehouse = 0;

            mineSemaphore = new SemaphoreSlim(2, 2);
            warehouseSemaphore = new SemaphoreSlim(1, 1);

            Task[] tasks = new Task[minersCount];

            Stopwatch stopwatch = new Stopwatch();

            stopwatch.Start();

            for (int i = 0; i < tasks.Length; i++)
            {
                int minerId = i + 1;

                tasks[i] = Task.Run(() => Miner(minerId));
            }

            Task.WaitAll(tasks);

            stopwatch.Stop();

            return stopwatch.Elapsed.TotalSeconds;
        }

        static void Miner(int id)
        {
            while (true)
            {
                int takenCoal = 0;

                mineSemaphore.Wait();

                lock (lockObject)
                {
                    if (coalDeposit <= 0)
                    {
                        mineSemaphore.Release();
                        break;
                    }

                    takenCoal = Math.Min(vehicleCapacity, coalDeposit);

                    coalDeposit -= takenCoal;
                }

                Thread.Sleep(takenCoal * 10);

                mineSemaphore.Release();

                Thread.Sleep(3000);

                warehouseSemaphore.Wait();

                Thread.Sleep(takenCoal * 10);

                lock (lockObject)
                {
                    warehouse += takenCoal;
                }

                warehouseSemaphore.Release();
            }
        }
    }
}