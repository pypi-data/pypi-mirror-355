PORT=$(python -c "import random; print(random.randint(50000, 60000))")
echo "La compétition se passe sur 127.0.0.1:$PORT"

python  -m space_collector.killall.py
find . -name "*.log" -exec rm \{} \;

python -m space_collector.game.server -p $PORT &
python -m space_collector.viewer -p $PORT &
# https://www.speedscope.app/
# py-spy record -o profile.data --format speedscope -- python -m space_collector.viewer -p $PORT &
#python -m space_collector.viewer -p $PORT --small-window &
sleep 2
# python -m space_collector.serial2tcp -p $PORT &
python /home/vincent/Documents/programmation/space_collector_player/sample_player_client.py -p $PORT -u "STAR WARS" --winner &
sleep 1
python /home/vincent/Documents/programmation/space_collector_player/sample_player_client.py -p $PORT -u "STAR TREK" --rotation-fire &
sleep 1
python /home/vincent/Documents/programmation/space_collector_player/sample_player_client.py -p $PORT -u DUNE &
sleep 1
python /home/vincent/Documents/programmation/space_collector_player/sample_player_client.py -p $PORT -u "INTERSTELLAR" &

sleep 330
python -m space_collector.killall
