import math
import time
import threading
from minecraft.networking.connection import Connection
from minecraft.networking.packets.serverbound.play import (
    UseEntityPacket, ClientStatusPacket, PlayerPositionAndLookPacket, UseItemOnBlockPacket, PlayerDiggingPacket, ChatPacket, SpawnMobPacket, EntityDestroyPacket, EntityTeleportPacket, SpawnPlayerPacket
)
import random

class FullRealBot:
    def __init__(self, host, port, username):
        self.connection = Connection(host, port, username=username)
        self.username = username
        self.entities = {}  # id -> (x,y,z)
        self.entities_lock = threading.Lock()
        self.bot_entity_id = None
        self.bot_pos = (0, 0, 0)
        self.running = False

        # Listeners para atualizar entidades e posição
        self.connection.register_packet_listener(self._on_spawn_mob, SpawnMobPacket)
        self.connection.register_packet_listener(self._on_spawn_player, SpawnPlayerPacket)
        self.connection.register_packet_listener(self._on_entity_destroy, EntityDestroyPacket)
        self.connection.register_packet_listener(self._on_entity_teleport, EntityTeleportPacket)

    def start(self):
        self.connection.connect()
        self.running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        while self.running:
            self.connection.network_process()
            time.sleep(0.01)

    def _on_spawn_mob(self, packet):
        with self.entities_lock:
            self.entities[packet.entity_id] = (packet.x, packet.y, packet.z)

    def _on_spawn_player(self, packet):
        with self.entities_lock:
            self.entities[packet.entity_id] = (packet.x, packet.y, packet.z)
            if packet.name == self.username:
                self.bot_entity_id = packet.entity_id
                self.bot_pos = (packet.x, packet.y, packet.z)

    def _on_entity_destroy(self, packet):
        with self.entities_lock:
            for eid in packet.entity_ids:
                self.entities.pop(eid, None)

    def _on_entity_teleport(self, packet):
        with self.entities_lock:
            if packet.entity_id in self.entities:
                self.entities[packet.entity_id] = (packet.x, packet.y, packet.z)
            if packet.entity_id == self.bot_entity_id:
                self.bot_pos = (packet.x, packet.y, packet.z)

    # Movimento para posição absoluta
    def move_to(self, x, y, z):
        packet = PlayerPositionAndLookPacket()
        packet.x = x
        packet.y = y
        packet.z = z
        packet.yaw = 0
        packet.pitch = 0
        packet.flags = 0
        packet.teleport_id = 0
        self.connection.write_packet(packet)
        self.bot_pos = (x, y, z)

    # Seguir jogador (exemplo simples que só pega a primeira entidade não bot)
    def follow_player(self, duration=10, interval=0.5):
        end_time = time.time() + duration
        while time.time() < end_time and self.running:
            with self.entities_lock:
                target_pos = None
                for eid, pos in self.entities.items():
                    if eid != self.bot_entity_id:
                        target_pos = pos
                        break
            if target_pos:
                self.move_to(*target_pos)
            time.sleep(interval)

    # Atacar entidade mais próxima até distância 10
    def attack_nearest_entity(self):
        with self.entities_lock:
            if not self.entities:
                return
            nearest_id = None
            nearest_dist = float('inf')
            bx, by, bz = self.bot_pos
            for eid, (ex, ey, ez) in self.entities.items():
                if eid == self.bot_entity_id:
                    continue
                dist = math.sqrt((ex - bx) ** 2 + (ey - by) ** 2 + (ez - bz) ** 2)
                if dist < nearest_dist and dist <= 10:
                    nearest_dist = dist
                    nearest_id = eid
            if nearest_id:
                packet = UseEntityPacket()
                packet.entity_id = nearest_id
                packet.type = UseEntityPacket.TYPE_ATTACK
                self.connection.write_packet(packet)

    # Respawn no servidor
    def respawn(self):
        packet = ClientStatusPacket()
        packet.action_id = ClientStatusPacket.PERFORM_RESPAWN
        self.connection.write_packet(packet)

    # Abrir baú / interagir com bloco (x,y,z = posição do bloco)
    def open_chest(self, x, y, z, face=1):
        packet = UseItemOnBlockPacket()
        packet.location = (x, y, z)
        packet.face = face
        packet.hand = 0  # mão principal
        packet.cursor_x = 0.5
        packet.cursor_y = 0.5
        packet.cursor_z = 0.5
        self.connection.write_packet(packet)

    # Minerar bloco na posição (x,y,z)
    def mine_block(self, x, y, z):
        # Start dig (status 0)
        packet = PlayerDiggingPacket()
        packet.status = PlayerDiggingPacket.STATUS_START_DESTROY_BLOCK
        packet.location = (x, y, z)
        packet.face = 1
        self.connection.write_packet(packet)
        time.sleep(0.2)
        # Finish dig (status 2)
        packet.status = PlayerDiggingPacket.STATUS_STOP_DESTROY_BLOCK
        self.connection.write_packet(packet)

    # Pular (alterar Y, enviar posição)
    def jump(self):
        x, y, z = self.bot_pos
        self.move_to(x, y + 1.2, z)  # subir
        time.sleep(0.2)
        self.move_to(x, y, z)  # voltar

    # Enviar mensagem no chat real (não comando)
    def send_chat_message(self, message):
        packet = ChatPacket()
        packet.message = message
        self.connection.write_packet(packet)

    # Desconectar
    def stop(self):
        self.running = False
        self.connection.disconnect()