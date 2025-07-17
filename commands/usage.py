import discord
from discord import app_commands, Embed
import datetime
import platform
import psutil
import humanize
import socket
import requests
import json
import os
import asyncio
from dotenv import load_dotenv
import time

load_dotenv()
my_admin = os.getenv('ADMIN_ID')
admin_user = int(my_admin) if my_admin else None
theme_color = 0x6f42c1

STATS_FILE = "usage_stats.json"
USAGE_MSG_FILE = 'usage_message.json'
UPDATE_INTERVAL = 30 # update in every 30 secs

class Usage(app_commands.Group):
    def __init__(self, tree: app_commands.CommandTree, bot: discord.Client):
        super().__init__(name="usage", description="check server usage")
        self.bot = bot
        self.start_time = datetime.datetime.now()
        self.net_start = psutil.net_io_counters()
        self.updating_task = None
        self.usage_message_info = self.load_usage_message_info()
        self.cumul = self.load_cumulative()
        self.last_cpu_times = psutil.cpu_times()
        self.last_power_calc_time = datetime.datetime.now()
        self.bot.loop.create_task(self.start_updating_task())

    def get_system_uptime(self):
        try:
            with open('/proc/uptime', 'r') as f: # fetch uptime this is for ubuntu
                uptime_seconds = float(f.readline().split()[0])
            return datetime.timedelta(seconds=uptime_seconds)
        except:
            return datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())

    async def get_accurate_cpu_usage(self):
        psutil.cpu_percent() 
        await asyncio.sleep(0.5)
        total = psutil.cpu_percent()
        return total

    async def get_per_core_usage(self): # get accurate per core cpu usage.
        psutil.cpu_percent(percpu=True)
        await asyncio.sleep(0.5) 
        return psutil.cpu_percent(percpu=True)

    def calculate_power_usage(self):
        try:
            psutil.cpu_percent()
            time.sleep(0.1)
            cpu_percent = psutil.cpu_percent()
            
            memory = psutil.virtual_memory()
            
            #  cpu frequency
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                current_freq = cpu_freq.current
            else:
                current_freq = 2000 
            
            cpu_count = psutil.cpu_count(logical=True)
            
            base_power = 5
            cpu_power = (cpu_percent / 100) * (current_freq / 1000) * 0.5 * cpu_count
            memory_power = (memory.percent / 100) * 2
            
            io_power = 0
            try:
                disk_io = psutil.disk_io_counters()
                net_io = psutil.net_io_counters()
                if disk_io and disk_io.read_bytes + disk_io.write_bytes > 0:
                    io_power += 2
                if net_io and net_io.bytes_sent + net_io.bytes_recv > 0:
                    io_power += 0.5
            except:
                pass
            
            total_power = base_power + cpu_power + memory_power + io_power
            return max(total_power, 1)
            
        except Exception as e:
            print(f"Error calculating power: {e}")
            return 1

    def load_cumulative(self):
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        return {"power_wh": 0.0, "bytes": 0}

    def save_cumulative(self):
        with open(STATS_FILE, "w") as f:
            json.dump(self.cumul, f)

    def load_usage_message_info(self):
        if os.path.exists(USAGE_MSG_FILE):
            with open(USAGE_MSG_FILE, 'r') as f:
                return json.load(f)
        return None

    def save_usage_message_info(self, info):
        with open(USAGE_MSG_FILE, 'w') as f:
            json.dump(info, f)

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('1.1.1.1', 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = 'N/A'
        finally:
            s.close()
        return ip

    async def start_updating_task(self):
        await self.bot.wait_until_ready()
        if self.usage_message_info:
            if not self.updating_task or self.updating_task.done():
                self.updating_task = self.bot.loop.create_task(self.update_usage_message_loop())

    async def update_usage_message_loop(self):
        while True:
            try:
                await self.update_usage_message()
            except Exception as e:
                print(f"Error updating usage message: {e}")
            await asyncio.sleep(UPDATE_INTERVAL)

    async def update_usage_message(self):
        if not self.usage_message_info:
            return
        channel = self.bot.get_channel(self.usage_message_info['channel_id'])
        if not channel:
            return
        try:
            message = await channel.fetch_message(self.usage_message_info['message_id'])
            embed = await self.build_usage_embed()
            await message.edit(embed=embed)
        except Exception:
            return

    async def build_usage_embed(self):
        now = datetime.datetime.now()
        uptime = self.get_system_uptime()
        hours_up = uptime.total_seconds() / 3600

        # power consumption since last update
        current_power = self.calculate_power_usage()
        time_diff = (now - self.last_power_calc_time).total_seconds() / 3600
        power_wh_since = current_power * time_diff
        self.last_power_calc_time = now

        net_now = psutil.net_io_counters()
        bytes_since = (net_now.bytes_sent - self.net_start.bytes_sent) + (net_now.bytes_recv - self.net_start.bytes_recv)

        self.cumul["power_wh"] += power_wh_since
        self.cumul["bytes"] += bytes_since
        self.save_cumulative()

        uname = platform.uname()
        cpu_percent = await self.get_accurate_cpu_usage()
        per_core = await self.get_per_core_usage()
        load1, load5, load15 = psutil.getloadavg()
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        hostname = socket.gethostname()
        try:
            public_ip = requests.get("https://api.ipify.org").text
        except:
            public_ip = "N/A"
        local_ip = self.get_local_ip()

        embed = Embed(title="<:Servers:1395546303035080714> Machine Usage Stats", color=theme_color)
        embed.add_field(name="<:System:1394572109988237392> OS", value=f"{uname.system} {uname.release}", inline=True)
        embed.add_field(name="<:Help_Icon:1207931111553105982> Hostname", value=hostname, inline=True)
        embed.add_field(name="<:Clock:1394589916352221278> System Uptime", value=str(uptime).split('.')[0], inline=True)

        embed.add_field(name="<:cpu:1394571630906183701>CPU Usage", value=f"{cpu_percent:.1f}%", inline=True)
        embed.add_field(name="<:cpu:1394571630906183701> Per-Core", value=", ".join(f"{p:.1f}%" for p in per_core), inline=True)
        embed.add_field(name="<:Warning:1392860065349763082> Load Avg (1m | 5m | 15m)", value=f"{load1:.2f} / {load5:.2f} / {load15:.2f}", inline=True)

        embed.add_field(name="<:ram:1394571721335504906> Memory Usage", value=f"{vm.percent}% of {humanize.naturalsize(vm.total, binary=True)}", inline=True)
        embed.add_field(name="<:disk:1394571662913044530> Disk Usage", value=f"{disk.percent}% of {humanize.naturalsize(disk.total, binary=True)}", inline=True)

        embed.add_field(name="<:online_web:1392690979915694200> Local IP", value=local_ip, inline=True)
        embed.add_field(name="<:online_web:1392690979915694200> Public IP", value=public_ip, inline=True)

        embed.add_field(
            name="<:emojigg_ETN:1394572161070530630> Since Boot (This Session)",
            value=f"Power: {power_wh_since:.2f} Wh ({power_wh_since/1000:.3f} kWh)\n"
                  f"Bandwidth: {bytes_since/1024**2:.2f} MB ({bytes_since/1024**3:.3f} GB)",
            inline=False
        )

        embed.add_field(
            name="<:emojigg_ETN:1394572161070530630> Cumulative Total",
            value=f"Power: {self.cumul['power_wh']:.2f} Wh ({self.cumul['power_wh']/1000:.3f} kWh)\n"
                  f"Bandwidth: {self.cumul['bytes']/1024**2:.2f} MB ({self.cumul['bytes']/1024**3:.3f} GB)",
            inline=False
        )

        embed.set_footer(text=f"Last Updated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        return embed

    @app_commands.command(name="home-srv1", description="show home server 1 usage")
    async def usage(self, interaction: discord.Interaction):
        if interaction.user.id != admin_user:
            await interaction.response.send_message(
                embed=Embed(description="🔐 Permission spell failed, try again with power.", color=theme_color),
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=False)
        embed = await self.build_usage_embed()

        # update old message
        if self.usage_message_info:
            channel = self.bot.get_channel(self.usage_message_info['channel_id'])
            if channel:
                try:
                    message = await channel.fetch_message(self.usage_message_info['message_id'])
                    await message.edit(embed=embed)
                    await interaction.followup.send("Usage message updated and will continue to update ig", ephemeral=True)
                    return
                except Exception:
                    pass  # pass a new msg if old dont exist

        msg = await interaction.channel.send(embed=embed)
        self.usage_message_info = { # save info of sent msg
            'guild_id': interaction.guild.id if interaction.guild else None,
            'channel_id': interaction.channel.id,
            'message_id': msg.id
        }
        self.save_usage_message_info(self.usage_message_info)
        await interaction.followup.send("Usage message created and will be updated automatically", ephemeral=True)

        if not self.updating_task or self.updating_task.done():
            self.updating_task = self.bot.loop.create_task(self.update_usage_message_loop())

async def setup(tree: app_commands.CommandTree, bot: discord.Client):
    usage_group = Usage(tree, bot)
    tree.add_command(usage_group)